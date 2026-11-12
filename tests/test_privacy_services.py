"""Run the privacy role while replacing host file and service operations."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ACTION = '''"""Record host operations without changing the test machine."""
import json
import os
from pathlib import Path
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        action = self._task.action.split('.')[-1]
        args = self._task.args
        with Path(os.environ['PRIVACY_OPERATIONS']).open('a') as output:
            output.write(json.dumps({'action': action, 'args': args}) + '\\n')
        installed = os.environ['PRIVACY_RSYSLOG'] == '1'
        if action == 'stat':
            return {'changed': False, 'stat': {'exists': installed}}
        if action == 'command':
            command = args.get('_raw_params', '')
            failed = 'rsyslogd' in command and (
                not installed or os.environ.get('PRIVACY_INVALID_CONFIG') == '1'
            )
            return {'changed': False, 'failed': failed, 'rc': int(failed)}
        return {'changed': True}
'''


def run_privacy(tmp_path: Path, installed: bool, invalid: bool = False):
    """Execute production role conditions and handlers against recorded OS boundaries."""
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    for module in ("stat", "file", "template", "cron", "lineinfile", "systemd", "command"):
        (plugins / f"{module}.py").write_text(ACTION)
    playbook = tmp_path / "privacy.yml"
    playbook.write_text(
        yaml.safe_dump(
            [
                {
                    "hosts": "localhost",
                    "gather_facts": False,
                    "roles": [str(ROOT / "roles/privacy")],
                    "vars": {
                        "privacy_history_clearing": {
                            "clear_bash_history": False,
                            "clear_system_history": False,
                            "disable_service_history": False,
                        },
                        "privacy_auto_cleanup": {
                            "enabled": False,
                            "frequency": "daily",
                            "clean_package_cache": False,
                        },
                        "privacy_advanced": {
                            "reduce_kernel_verbosity": False,
                            "disable_ssh_success_logs": True,
                            "clear_logs_on_shutdown": True,
                        },
                    },
                },
            ],
        ),
    )
    operations = tmp_path / "operations.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            str(playbook),
            "-i",
            "localhost,",
            "-c",
            "local",
        ],
        cwd=ROOT,
        env={
            **os.environ,
            "ANSIBLE_ACTION_PLUGINS": str(plugins),
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller"),
            "ANSIBLE_NOCOLOR": "1",
            "PRIVACY_OPERATIONS": str(operations),
            "PRIVACY_RSYSLOG": str(int(installed)),
            "PRIVACY_INVALID_CONFIG": str(int(invalid)),
        },
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    return result, [json.loads(line) for line in operations.read_text().splitlines()]


@pytest.mark.parametrize("installed", [False, True])
def test_privacy_without_or_with_rsyslog(tmp_path, installed):
    """Minimal images retain journald and cleanup settings without rsyslog operations."""
    result, operations = run_privacy(tmp_path, installed)
    assert result.returncode == 0, result.stdout + result.stderr
    writes = [operation["args"] for operation in operations if operation["action"] != "stat"]
    rsyslog = [args for args in writes if "rsyslog" in json.dumps(args)]
    assert bool(rsyslog) == installed
    assert {
        "path": "/etc/systemd/journald.conf",
        "regexp": "^#?Storage=",
        "line": "Storage=volatile",
        "backup": True,
    } in writes
    assert any(args.get("line") == "ForwardToSyslog=no" for args in writes)
    assert any(args.get("name") == "systemd-journald" for args in writes)
    assert any(args.get("dest") == "/usr/local/bin/privacy-log-cleanup.sh" for args in writes)
    assert any(args.get("dest") == "/usr/local/bin/privacy-auto-cleanup.sh" for args in writes)
    assert any(args.get("name") == "privacy-shutdown-cleanup.service" for args in writes)
    if installed:
        assert any(args.get("_raw_params") == "rsyslogd -N1" for args in writes)
        assert any(args.get("name") == "rsyslog" for args in writes)


def test_invalid_rsyslog_configuration_stops_deployment(tmp_path):
    """Keep rsyslog validation failures visible on systems where it is installed."""
    result, operations = run_privacy(tmp_path, True, invalid=True)
    assert result.returncode != 0
    assert "Test rsyslog configuration" in result.stdout
    assert not any(item["args"].get("name") == "rsyslog" for item in operations)
