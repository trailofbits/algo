# fmt: off
# ruff: noqa: W191
"""Exercise Oracle bootstrap commands against a simulated image firewall."""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parents[2]
IMAGE_RULES = [
	'-A INPUT -p tcp --dport 22 -j ACCEPT',
	'-A INPUT -j REJECT --reject-with icmp-host-prohibited',
	'-A OUTPUT -d 169.254.0.0/16 -j InstanceServices',
	'-A InstanceServices -d 169.254.0.2/32 -p tcp --dport 3260 -j ACCEPT',
	'-A InstanceServices -d 169.254.169.254/32 -p tcp --dport 80 -j ACCEPT',
	'-A InstanceServices -p tcp -j REJECT --reject-with tcp-reset',
]

MOCK_COMMAND = '''
import json
import os
import sys
from pathlib import Path

state_path = Path(os.environ['MOCK_FIREWALL_STATE'])
saved_path = Path(os.environ['MOCK_FIREWALL_SAVED'])
state = json.loads(state_path.read_text())
name = Path(sys.argv[0]).name
args = sys.argv[1:]
state['events'].append({
	'command': name,
	'args': args,
	'saved': saved_path.read_text() if saved_path.exists() else None,
})
status = 0
if name == 'iptables':
	if args[:2] == ['-C', 'INPUT']:
		status = int('-A INPUT ' + ' '.join(args[2:]) not in state['rules'])
	elif args[:3] == ['-I', 'INPUT', '1']:
		state['rules'].insert(0, '-A INPUT ' + ' '.join(args[3:]))
	else:
		raise AssertionError('Unexpected iptables command: ' + repr(args))
elif name == 'iptables-save':
	print('*filter\\n' + '\\n'.join(state['rules']) + '\\nCOMMIT')
state_path.write_text(json.dumps(state))
sys.exit(status)
'''


def render_cloud_init(provider, port):
	"""Render the real templates while substituting only the public key lookup."""
	env = Environment(loader=FileSystemLoader(ROOT), undefined=StrictUndefined)
	variables = {'algo_provider': provider, 'ssh_port': port, 'SSH_keys': {'public': 'mock.pub'}}

	def lookup(kind, path):
		"""Keep template lookup real and avoid reading any deployment credentials."""
		if kind == 'file':
			assert path == 'mock.pub'
			return 'ssh-ed25519 MOCK_PUBLIC_KEY'
		assert kind == 'template'
		return env.get_template(path).render(**variables)

	env.globals['lookup'] = lookup
	return yaml.safe_load(env.get_template('files/cloud-init/base.yml').render(**variables))


@pytest.fixture
def bootstrap(tmp_path):
	"""Run cloud-init shell commands with isolated executable mocks and rule files."""
	state_path = tmp_path / 'state.json'
	saved_path = tmp_path / 'rules.v4'
	state_path.write_text(json.dumps({'rules': IMAGE_RULES.copy(), 'events': []}))
	bin_path = tmp_path / 'bin'
	bin_path.mkdir()
	for command in ('iptables', 'iptables-save', 'ufw', 'sudo', 'systemctl'):
		executable = bin_path / command
		executable.write_text('#!' + sys.executable + '\n' + MOCK_COMMAND)
		executable.chmod(0o755)
	env = {
		**os.environ,
		'PATH': str(bin_path),
		'MOCK_FIREWALL_STATE': str(state_path),
		'MOCK_FIREWALL_SAVED': str(saved_path),
	}

	def run(provider='oracle', port=4160):
		"""Preserve shell behavior, redirecting only the persistent rule destination."""
		config = render_cloud_init(provider, port)
		commands = [
			shlex.join(command) if isinstance(command, list) else command
			for command in config['runcmd']
		]
		script = '\n'.join(commands).replace('/etc/iptables/rules.v4', shlex.quote(str(saved_path)))
		subprocess.run(['/bin/sh', '-e', '-c', script], env=env, check=True, capture_output=True, text=True)
		return json.loads(state_path.read_text()), saved_path

	return run


@pytest.mark.parametrize('port', [4160, 2222])
def test_oracle_opens_configured_ssh_port_and_preserves_image_rules(bootstrap, port):
	"""A first matching SSH accept must precede OCI's reject without losing storage rules."""
	state, saved_path = bootstrap(port=port)
	assert state['rules'] == [f'-A INPUT -p tcp --dport {port} -j ACCEPT', *IMAGE_RULES]
	assert all(event['command'] != 'ufw' for event in state['events'])
	assert saved_path.read_text() == '*filter\n' + '\n'.join(state['rules']) + '\nCOMMIT\n'
	restart = next(event for event in state['events'] if event['command'] == 'systemctl')
	assert restart['args'] == ['restart', 'sshd.service']
	assert restart['saved'] == saved_path.read_text()


def test_oracle_bootstrap_does_not_duplicate_ssh_rule(bootstrap):
	"""A repeated bootstrap leaves one SSH exception and the original image rules."""
	bootstrap()
	state, _ = bootstrap()
	assert state['rules'] == ['-A INPUT -p tcp --dport 4160 -j ACCEPT', *IMAGE_RULES]
	assert sum(event['args'][:1] == ['-I'] for event in state['events']) == 1


@pytest.mark.parametrize('provider', ['ec2', 'gce', 'local'])
def test_other_providers_keep_existing_ufw_bootstrap(bootstrap, provider):
	"""Oracle's inherited firewall handling must stay scoped to Oracle images."""
	state, saved_path = bootstrap(provider=provider)
	assert [event['command'] for event in state['events']] == ['ufw', 'sudo', 'systemctl']
	assert state['events'][0]['args'] == ['--force', 'reset']
	assert state['rules'] == IMAGE_RULES
	assert not saved_path.exists()
