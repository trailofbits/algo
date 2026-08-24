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
    for task in tasks:
        if task.get("name") == name:
            return task
        for section in ("block", "rescue", "always"):
            if section in task:
                try:
                    return task_named(task[section], name)
                except StopIteration:
                    pass
    raise StopIteration(name)


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
    assert argv[0] == "{{ ansible_playbook_python }}"
    assert argv[1] == "-c"
    assert "segno.make(sys.stdin.read(), micro=False)" in argv[2]
    assert argv[3] == "{{ wireguard_qr_job.path }}"
    assert "creates" not in generate["command"]
    assert generate["no_log"] is True
    assert "shell" not in generate


def test_qr_secret_configuration_is_supplied_via_stdin_not_process_arguments():
    tasks = load_tasks(QR_TASKS)
    generate = task_named(tasks, "Generate QR codes")
    argv = generate["command"]["argv"]

    assert "client.conf.j2" not in " ".join(argv)
    assert generate["command"]["stdin"] == "{{ lookup('template', 'client.conf.j2') }}"
    assert generate["command"]["stdin_add_newline"] is False


def test_qr_output_is_allocated_securely_before_segno_writes_secrets():
    tasks = load_tasks(QR_TASKS)
    prepare = task_named(tasks, "Allocate secure QR output files")
    generate = task_named(tasks, "Generate QR codes")

    tempfile = prepare["ansible.builtin.tempfile"]
    assert tempfile["state"] == "file"
    assert tempfile["path"] == "{{ wireguard_config_path }}"
    assert tempfile["prefix"] == ".algo-qr-"
    assert tempfile["suffix"] == ".png"
    assert prepare["no_log"] is True
    assert generate["command"]["argv"][3] == "{{ wireguard_qr_job.path }}"


def test_qr_integration_play_covers_failure_paths():
    playbook = (ROOT / "tests/integration/test_qr_generation.yml").read_text(encoding="utf-8")
    assert "Verify invalid QR output path fails closed" in playbook
    assert "qr_invalid_path_rejected" in playbook
    assert "no_log: true" in playbook


def test_qr_uses_secure_unique_temporary_files_and_atomic_install():
    tasks = load_tasks(QR_TASKS)
    serialized = yaml.safe_dump(tasks)

    assert "ansible.builtin.tempfile" in serialized
    assert "state: touch" not in serialized
    assert "wireguard_qr_job.path" in serialized
    assert "follow: false" in serialized
    assert "unsafe_writes: false" in serialized


def test_temporary_qr_files_are_removed_even_when_generation_fails():
    tasks = load_tasks(QR_TASKS)
    generation_block = task_named(tasks, "Generate and install QR codes safely")

    assert "block" in generation_block
    assert "always" in generation_block
    assert any(task.get("name") == "Remove temporary QR files" for task in generation_block["always"])


def test_concurrent_qr_generation_never_installs_an_unwritten_tempfile():
    tasks = load_tasks(QR_TASKS)
    generate = task_named(tasks, "Generate QR codes")
    install = task_named(tasks, "Install generated QR codes")

    assert "creates" not in generate["command"]
    assert generate["changed_when"] is True
    assert install["copy"]["force"] is False


def test_qr_generation_is_serialized_by_an_atomic_lock_directory():
    tasks = load_tasks(QR_TASKS)
    acquire = task_named(tasks, "Acquire QR generation lock atomically")
    locked = task_named(tasks, "Generate QR codes under lock")
    argv = acquire["ansible.builtin.command"]["argv"]

    assert argv[0] == "{{ ansible_playbook_python }}"
    assert argv[1] == "-c"
    assert "fcntl.flock" in argv[2]
    assert "os.mkdir" in argv[2]
    assert argv[3:] == [
        "{{ wireguard_config_path }}/.algo-qr.lock",
        "{{ wireguard_config_path }}/.algo-qr-recovery.lock",
        "900",
    ]
    assert any(task.get("name") == "Release QR generation lock" for task in locked["always"])


def test_qr_lock_recovers_stale_state_inside_the_same_flock_critical_section():
    tasks = load_tasks(QR_TASKS)
    acquire = task_named(tasks, "Acquire QR generation lock atomically")
    code = acquire["ansible.builtin.command"]["argv"][2]

    assert "time.time()" in code
    assert "os.stat" in code
    assert "os.rmdir" in code
    assert "fcntl.LOCK_EX" in code


def test_generated_qr_permissions_are_explicitly_restricted():
    tasks = load_tasks(QR_TASKS)
    permissions = task_named(tasks, "Restrict QR code permissions")

    assert permissions["file"] == {
        "path": "{{ wireguard_config_path }}/{{ item }}.png",
        "mode": "0600",
    }
