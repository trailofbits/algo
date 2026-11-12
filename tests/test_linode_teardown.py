"""Run Linode teardown through real Ansible tasks and the SDK against a local API."""

import importlib.util
import json
import os
import secrets
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
INSTANCE = {"id": 123, "label": "test-vpn", "interface_generation": "legacy_config"}
ENV_TOKEN = secrets.token_hex(16)
ARG_TOKEN = secrets.token_hex(16)
URI_REDIRECT = '''"""Redirect region discovery to the local HTTP fixture."""
import os
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        arguments = dict(self._task.args)
        assert arguments['url'] == 'https://api.linode.com/v4/regions'
        arguments['url'] = os.environ['LINODE_API_URL'] + 'v4/regions'
        return self._execute_module(
            module_name='ansible.builtin.uri', module_args=arguments, task_vars=task_vars
        )
'''


class LinodeAPIHandler(BaseHTTPRequestHandler):
    """Serve only the HTTP operations needed by the production deletion module."""

    def do_GET(self):
        path = urlsplit(self.path).path
        self.server.requests.append(("GET", path, dict(self.headers)))
        data = []
        if path == "/v4/regions":
            if self.server.state["regions_error"]:
                self.respond(503, {"errors": [{"reason": "Region discovery unavailable"}]})
                return
            data = [{"id": "us-east"}]
        elif path == "/v4/linode/instances":
            data = [INSTANCE] if self.server.state["exists"] else []
        elif path not in {
            "/v4/linode/instances/123/configs",
            "/v4/linode/instances/123/disks",
            "/v4/linode/instances/123/ips",
        }:
            self.respond(404, {"errors": [{"reason": "Unexpected API request"}]})
            return
        self.respond(200, {"data": data, "page": 1, "pages": 1, "results": len(data)})

    def do_DELETE(self):
        self.server.requests.append(("DELETE", self.path, dict(self.headers)))
        if self.path != "/v4/linode/instances/123":
            self.respond(404, {"errors": [{"reason": "Unexpected delete target"}]})
        elif self.server.state["delete_error"]:
            self.respond(403, {"errors": [{"reason": "Deletion denied by Linode"}]})
        else:
            self.respond(200, {})

    def respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *_arguments):
        return


@pytest.fixture
def linode_api():
    """Serve instance lookup/deletion while recording the real SDK's requests."""
    if importlib.util.find_spec("linode_api4") is None:
        if os.environ.get("ALGO_CLOUD_SMOKE") == "1":
            pytest.fail("Install the linode extra before running required cloud tests")
        pytest.skip("Install the linode extra to run the Linode API regression")
    server = ThreadingHTTPServer(("127.0.0.1", 0), LinodeAPIHandler)
    server.requests = []
    server.state = {"exists": True, "delete_error": False, "regions_error": False}
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/", server.requests, server.state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture
def linode_workspace(tmp_path):
    """Copy production playbooks without any SSH keys or a stored deployment region."""
    for filename in ("destroy.yml", "config.cfg"):
        shutil.copy(ROOT / filename, tmp_path)
    (tmp_path / "playbooks").mkdir()
    shutil.copy(ROOT / "playbooks/rescue.yml", tmp_path / "playbooks")
    shutil.copytree(ROOT / "roles/cloud-linode", tmp_path / "roles/cloud-linode")
    server = tmp_path / "configs/192.0.2.1"
    server.mkdir(parents=True)
    (server / ".config.yml").write_text("algo_provider: linode\nalgo_server_name: test-vpn\n")
    (server / "client.conf").write_text("keep this configuration if deletion fails\n")
    binary = tmp_path / "uv"
    binary.write_text(
        f"#!{sys.executable}\nimport sys\n"
        "assert sys.argv[1:] == ['sync', '--locked', '--inexact', '--extra', 'linode']\n",
    )
    binary.chmod(0o755)
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "uri.py").write_text(URI_REDIRECT)
    return tmp_path


def run_playbook(workspace: Path, endpoint: str, variables: dict, *, playbook="destroy.yml"):
    """Run production tasks, replacing only package installation and network endpoints."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith("LINODE_")}
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            str(workspace / playbook),
            "-i",
            "localhost,",
            "-c",
            "local",
            "-e",
            json.dumps({"ansible_python_interpreter": sys.executable, **variables}),
        ],
        cwd=workspace,
        env={
            **environment,
            "PATH": f"{workspace}:{os.environ['PATH']}",
            "ANSIBLE_ACTION_PLUGINS": str(workspace / "plugins"),
            "ANSIBLE_LOCAL_TEMP": str(workspace / "controller"),
            "ANSIBLE_REMOTE_TEMP": str(workspace / "remote"),
            "LINODE_API_URL": endpoint,
            "LINODE_API_TOKEN": ENV_TOKEN,
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


@pytest.mark.parametrize("explicit_token", [False, True])
@pytest.mark.parametrize("regions_error", [False, True])
def test_destroy_needs_only_auth(linode_workspace, linode_api, explicit_token, regions_error):
    """Delete using only the saved label and credentials, even if region discovery is down."""
    endpoint, requests, state = linode_api
    state["regions_error"] = regions_error
    variables = {"server_ip": "192.0.2.1", "confirm_destroy": True}
    expected_token = ENV_TOKEN
    if explicit_token:
        variables["linode_token"] = expected_token = ARG_TOKEN
    result = run_playbook(linode_workspace, endpoint, variables)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (linode_workspace / "configs/192.0.2.1").exists()
    assert not (linode_workspace / "configs/algo.pem.pub").exists()
    assert all(path != "/v4/regions" for _, path, _ in requests)
    assert [path for method, path, _ in requests if method == "DELETE"] == [
        "/v4/linode/instances/123",
    ]
    assert all(headers["Authorization"] == f"Bearer {expected_token}" for _, _, headers in requests)
    lookup = next(headers for _, path, headers in requests if path == "/v4/linode/instances")
    assert json.loads(lookup["X-Filter"])["label"] == "test-vpn"


def test_already_absent_instance_removes_local_config(linode_workspace, linode_api):
    """Complete teardown when the provider no longer has a matching instance."""
    endpoint, requests, state = linode_api
    state["exists"] = False
    result = run_playbook(
        linode_workspace,
        endpoint,
        {"server_ip": "192.0.2.1", "confirm_destroy": True},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (linode_workspace / "configs/192.0.2.1").exists()
    assert [(method, path) for method, path, _ in requests] == [("GET", "/v4/linode/instances")]


def test_failed_delete_keeps_local_config(linode_workspace, linode_api):
    """Retain client files when the provider rejects deletion."""
    endpoint, requests, state = linode_api
    state["delete_error"] = True
    result = run_playbook(
        linode_workspace,
        endpoint,
        {"server_ip": "192.0.2.1", "confirm_destroy": True},
    )
    assert result.returncode != 0
    assert "Deletion denied by Linode" in result.stdout
    assert any(method == "DELETE" for method, _, _ in requests)
    assert (linode_workspace / "configs/192.0.2.1/client.conf").read_text().startswith("keep this")


def test_unconfirmed_delete_makes_no_api_calls(linode_workspace, linode_api):
    """Keep the explicit confirmation gate before any cloud resource is deleted."""
    endpoint, requests, _ = linode_api
    result = run_playbook(
        linode_workspace,
        endpoint,
        {"server_ip": "192.0.2.1", "confirm_destroy": False},
    )
    assert result.returncode != 0
    assert "Destroy aborted by user" in result.stdout
    assert requests == []
    assert (linode_workspace / "configs/192.0.2.1/client.conf").exists()


def test_deployment_still_reads_credentials_region_and_key(linode_workspace, linode_api):
    """Keep deployment setup intact when its credential tasks are shared with teardown."""
    endpoint, requests, _ = linode_api
    key = linode_workspace / "public.pub"
    key.write_text("ssh-ed25519 test-public-key")
    tasks = [
        {"ansible.builtin.import_tasks": "roles/cloud-linode/tasks/prompts.yml"},
        {
            "ansible.builtin.assert": {
                "that": [
                    f"algo_linode_token == '{ARG_TOKEN}'",
                    "algo_linode_region == 'us-east'",
                    "public_key == 'ssh-ed25519 test-public-key'",
                ]
            }
        },
    ]
    playbook = [{"hosts": "localhost", "gather_facts": False, "tasks": tasks}]
    (linode_workspace / "deploy-prompts.yml").write_text(yaml.safe_dump(playbook))
    result = run_playbook(
        linode_workspace,
        endpoint,
        {"linode_token": ARG_TOKEN, "region": "us-east", "SSH_keys": {"public": str(key)}},
        playbook="deploy-prompts.yml",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [(method, path) for method, path, _ in requests] == [("GET", "/v4/regions")]
