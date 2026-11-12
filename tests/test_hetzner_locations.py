"""Exercise Hetzner discovery through the real collection and Ansible tasks."""

import importlib
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar, trust_as_template

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "roles/cloud-hetzner/tasks/prompts.yml"


@pytest.fixture
def hetzner_api():
    for dependency in ("requests", "dateutil"):
        if os.environ.get("ALGO_CLOUD_SMOKE") == "1":
            importlib.import_module(dependency)
        else:
            pytest.importorskip(dependency, reason="Run with the hetzner extra for API integration tests")
    requests = []
    pages = [[{"name": "nbg1", "description": "Nuremberg"}]]
    errors = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            requests.append(url.path)
            if errors:
                body = {"error": {"code": "unauthorized", "message": "Invalid API token"}}
                self.send_response(401)
            elif url.path == "/v1/locations":
                page = int(parse_qs(url.query).get("page", ["1"])[0])
                locations = [
                    dict(id=index + 1, country="DE", city="Test", **location)
                    for index, location in enumerate(pages[page - 1])
                ]
                body = {
                    "locations": locations,
                    "meta": {
                        "pagination": {
                            "page": page,
                            "per_page": 1,
                            "next_page": page + 1 if page < len(pages) else None,
                        }
                    },
                }
                self.send_response(200)
            else:
                body = {"error": {"code": "deprecated_api_endpoint", "message": "API removed"}}
                self.send_response(410)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def log_message(self, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", pages, requests, errors
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("scenario", ["explicit", "default", "fallback", "empty", "unauthorized"])
def test_hetzner_location_discovery(tmp_path: Path, hetzner_api, scenario: str):
    endpoint, pages, requests, errors = hetzner_api
    pages[:] = [[{"name": "hel1", "description": "Helsinki"}]]
    expected = "hel1"
    if scenario in {"explicit", "default"}:
        pages.append([{"name": "nbg1", "description": "Nuremberg"}])
        expected = "nbg1" if scenario == "default" else "hel1"
    if scenario == "empty":
        pages[:] = [[]]
    if scenario == "unauthorized":
        errors.append(True)
    variables = {"hcloud_token": "test-token", "ansible_python_interpreter": sys.executable}
    if scenario == "explicit":
        variables["region"] = "hel1"
    tasks = [
        {"ansible.builtin.import_tasks": str(PROMPTS)},
        {"ansible.builtin.assert": {"that": f"algo_hcloud_region == '{expected}'"}},
    ]
    playbook = tmp_path / "locations.yml"
    playbook.write_text(yaml.safe_dump([{"hosts": "localhost", "gather_facts": False, "tasks": tasks}]))
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
            "-e",
            json.dumps(variables),
        ],
        env={
            **os.environ,
            "HCLOUD_ENDPOINT": endpoint,
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller-tmp"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "module-tmp"),
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = result.stdout + result.stderr
    if scenario in {"empty", "unauthorized"}:
        assert result.returncode != 0
        expected_error = "Hetzner returned no locations" if scenario == "empty" else "Invalid API token"
        assert expected_error in output
    else:
        assert result.returncode == 0, output
    assert requests == ["/v1/locations"] * len(pages)


@pytest.mark.parametrize("choice,valid", [("1", True), ("2", True), ("0", False), ("3", False), ("x", False)])
def test_hetzner_location_selection(choice: str, valid: bool):
    loader = DataLoader()
    tasks = loader.load_from_file(str(PROMPTS), trusted_as_template=True)
    variables = {
        "hcloud_regions": [{"name": "hel1"}, {"name": "nbg1"}],
        "_algo_region": {"user_input": choice},
        "default_region": 2,
    }
    templar = Templar(loader=loader, variables=variables)
    validation = next(task["assert"] for task in tasks if "Validate" in task.get("name", ""))
    accepted = all(templar.template(trust_as_template("{{ " + condition + " }}")) for condition in validation["that"])
    assert accepted == valid
    if valid:
        selected = templar.template(tasks[-1]["set_fact"]["algo_hcloud_region"])
        assert selected == {"1": "hel1", "2": "nbg1"}[choice]
