"""Exercise Azure authentication and region selection with real Ansible tasks."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def run_tasks(
    tmp_path: Path,
    tasks: list[str],
    variables: dict,
    environment: dict,
) -> subprocess.CompletedProcess:
    """Run production preflight tasks with CLI output supplied at the process boundary."""
    playbook = tmp_path / "preflight.yml"
    output = tmp_path / "result.json"
    directory = ROOT / "roles/cloud-azure/tasks"
    task_list = [{"ansible.builtin.import_tasks": str(directory / task)} for task in tasks]
    result_template = "{{ {'subscription': subscription_id, "
    result_template += "'region': algo_region | default('')} | to_json }}"
    task_list.append(
        {
            "ansible.builtin.copy": {
                "content": result_template,
                "dest": str(output),
                "mode": "0600",
            },
        },
    )
    play = {"hosts": "localhost", "gather_facts": False, "tasks": task_list}
    playbook.write_text(yaml.safe_dump([play]))
    env = {key: value for key, value in os.environ.items() if not key.startswith("AZURE_")}
    env.update(environment)
    env.update(
        {
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "remote"),
            "ANSIBLE_NOCOLOR": "1",
        },
    )
    return subprocess.run(
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
            json.dumps({"ansible_python_interpreter": sys.executable, **variables}),
        ],
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


@pytest.mark.parametrize(
    ("explicit", "environ", "cli", "exit_code", "expected"),
    [
        (
            "argument-subscription",
            "environment-subscription",
            "cli-subscription",
            0,
            "argument-subscription",
        ),
        ("", "environment-subscription", "cli-subscription", 0, "environment-subscription"),
        ("", "", "cli-subscription\n", 0, "cli-subscription"),
        ("", "", "", 0, None),
        ("", "", "", 1, None),
    ],
)
def test_subscription_precedence(*, tmp_path, explicit, environ, cli, exit_code, expected):
    """Prefer explicit settings, then the environment, then the active CLI account."""
    binary = tmp_path / "az"
    called = tmp_path / "called"
    binary.write_text(
        f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\n"
        f"Path({str(called)!r}).write_text(' '.join(sys.argv[1:]))\n"
        f"sys.stdout.write({cli!r})\nsys.exit({exit_code})\n",
    )
    binary.chmod(0o755)
    result = run_tasks(
        tmp_path,
        ["auth.yml"],
        {"azure_subscription_id": explicit},
        {"AZURE_SUBSCRIPTION_ID": environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"},
    )
    if expected:
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads((tmp_path / "result.json").read_text())["subscription"] == expected
    else:
        assert result.returncode != 0
        assert "Unable to read the active Azure subscription" in result.stdout
    assert called.exists() == (not explicit and not environ)
    if called.exists():
        assert called.read_text() == "account show --query id --output tsv"


def test_missing_azure_cli(tmp_path):
    """Fail with recovery instructions when neither subscription nor CLI is available."""
    result = run_tasks(tmp_path, ["auth.yml"], {}, {"PATH": str(tmp_path)})
    assert result.returncode != 0
    assert "Unable to read the active Azure subscription" in result.stdout
    assert "AZURE_SUBSCRIPTION_ID" in result.stdout


def location(name, region_type="Physical"):
    """Build the public fields returned by Azure's subscription locations endpoint."""
    return {"name": name, "regionalDisplayName": name, "metadata": {"regionType": region_type}}


@pytest.mark.parametrize(
    ("choice", "region", "expected"),
    [
        ("", None, "eastus"),
        ("  ", None, "eastus"),
        ("1", None, "eastus"),
        ("2", None, "westus"),
        ("0", None, None),
        ("-1", None, None),
        ("3", None, None),
        ("1.5", None, None),
        ("garbage", None, None),
        ("", "westus", "westus"),
        ("", "global", None),
        ("", "eastusstage", None),
    ],
)
def test_region_selection(tmp_path, choice, region, expected):
    """Filter logical and staging locations and reject malformed or out-of-range input."""
    variables = {
        "subscription_id": "test-subscription",
        "azure_locations": {
            "response": [
                location("westus"),
                location("global", "Logical"),
                location("eastusstage"),
                location("eastusstg"),
                location("eastus2euap"),
                location("eastus"),
                {"name": "missing-metadata"},
            ],
        },
        "_algo_region": {"user_input": choice},
    }
    if region is not None:
        variables["region"] = region
    result = run_tasks(tmp_path, ["regions.yml", "select_region.yml"], variables, {})
    if expected:
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads((tmp_path / "result.json").read_text())["region"] == expected
    else:
        assert result.returncode != 0
        messages = ("Invalid Azure region selection", "available physical region")
        assert any(message in result.stdout for message in messages)


@pytest.mark.parametrize("locations", [[location("westus")], [], [location("global", "Logical")]])
def test_default_without_eastus(tmp_path, locations):
    """Use the first available physical region, or fail before presenting an empty menu."""
    result = run_tasks(
        tmp_path,
        ["regions.yml", "select_region.yml"],
        {"subscription_id": "test", "azure_locations": {"response": locations}},
        {},
    )
    if locations and locations[0]["name"] == "westus":
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads((tmp_path / "result.json").read_text())["region"] == "westus"
    else:
        assert result.returncode != 0
        assert "Azure returned no physical regions" in result.stdout
