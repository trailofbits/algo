"""Security and reliability contract for WireGuard QR generation."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
QR_TASKS = ROOT / "roles" / "wireguard" / "tasks" / "qr.yml"
MAIN_TASKS = ROOT / "roles" / "wireguard" / "tasks" / "main.yml"


def load_tasks(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def task_named(tasks: list[dict], name: str) -> dict:
    return next(task for task in tasks if task.get("name") == name)


def test_main_role_includes_dedicated_qr_tasks():
    tasks = load_tasks(MAIN_TASKS)
    update_block = next(task["block"] for task in tasks if "block" in task and task.get("tags") == "update-users")
    local_block = next(task["block"] for task in update_block if "block" in task)

    include = task_named(local_block, "Generate WireGuard QR codes")

    assert include["include_tasks"] == "qr.yml"


def test_segno_preflight_is_next_to_playbook_python_and_actionable():
    tasks = load_tasks(QR_TASKS)
    preflight = task_named(tasks, "Check for the Segno QR generator")
    requirement = task_named(tasks, "Require the Segno QR generator")

    assert preflight["stat"]["path"] == "{{ ansible_playbook_python | dirname }}/segno"
    assert preflight["register"] == "wireguard_segno"
    assert requirement["assert"]["that"] == [
        "wireguard_segno.stat.exists",
        "wireguard_segno.stat.isreg",
        "wireguard_segno.stat.executable",
    ]
    message = requirement["assert"]["fail_msg"].lower()
    assert "segno" in message
    assert "ansible_playbook_python" in message
    assert "install" in message
    assert "failed_when" not in requirement
    assert "ignore_errors" not in requirement


def test_missing_or_invalid_segno_cannot_fall_back_to_path_or_be_ignored():
    tasks = load_tasks(QR_TASKS)
    preflight = task_named(tasks, "Check for the Segno QR generator")
    generate = task_named(tasks, "Generate QR codes")

    assert preflight["stat"]["path"].startswith("{{ ansible_playbook_python | dirname }}")
    assert "get_command" not in preflight["stat"]
    assert "failed_when" not in generate
    assert "ignore_errors" not in generate


def test_qr_generation_uses_argv_hides_configuration_and_is_idempotent():
    tasks = load_tasks(QR_TASKS)
    generate = task_named(tasks, "Generate QR codes")

    argv = generate["command"]["argv"]
    assert argv[0] == "{{ ansible_playbook_python | dirname }}/segno"
    assert argv[1:3] == ["--scale=5", "--output={{ wireguard_config_path }}/.{{ item }}.tmp.png"]
    assert argv[3] == "{{ lookup('template', 'client.conf.j2') }}"
    assert generate["command"]["creates"] == "{{ wireguard_config_path }}/{{ item }}.png"
    assert generate["no_log"] is True
    assert "shell" not in generate


def test_qr_output_is_precreated_securely_before_segno_writes_secrets():
    tasks = load_tasks(QR_TASKS)
    prepare = task_named(tasks, "Prepare secure QR output")
    generate = task_named(tasks, "Generate QR codes")

    assert prepare["file"]["state"] == "touch"
    assert prepare["file"]["mode"] == "0600"
    assert prepare["file"]["path"] == "{{ wireguard_config_path }}/.{{ item }}.tmp.png"
    assert generate["command"]["argv"][2] == "--output={{ wireguard_config_path }}/.{{ item }}.tmp.png"


def test_generated_qr_permissions_are_explicitly_restricted():
    tasks = load_tasks(QR_TASKS)
    permissions = task_named(tasks, "Restrict QR code permissions")

    assert permissions["file"] == {
        "path": "{{ wireguard_config_path }}/{{ item }}.png",
        "mode": "0600",
    }
