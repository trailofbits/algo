"""Security and reliability contract for WireGuard QR generation."""

import os
import re
import subprocess
import sys
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
    assert generate["loop_control"]["index_var"] == "index"
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


def test_qr_usernames_are_safe_single_path_components():
    tasks = load_tasks(QR_TASKS)
    validation = task_named(tasks, "Validate WireGuard QR usernames")

    assert validation["loop"] == "{{ wireguard_users }}"
    conditions = validation["assert"]["that"]
    assert "item is string" in conditions
    regex_condition = next(condition for condition in conditions if condition.startswith("item is regex("))
    pattern = regex_condition.removeprefix("item is regex('").removesuffix("')")
    assert pattern.endswith(r"\Z")
    assert re.search(pattern, "alice")
    for unsafe in ("alice\n", "../alice", "alice/bob", "alice\x00"):
        assert not re.search(pattern, unsafe)


def test_existing_qr_outputs_must_be_regular_non_symlink_files():
    tasks = load_tasks(QR_TASKS)
    inspect = task_named(tasks, "Inspect existing QR codes")
    validation = task_named(tasks, "Validate existing QR code files")

    assert inspect["stat"]["follow"] is False
    conditions = validation["assert"]["that"]
    assert "not item.stat.exists or (item.stat.isreg and not item.stat.islnk)" in conditions


def test_qr_integration_play_covers_failure_paths():
    playbook = (ROOT / "tests/integration/test_qr_generation.yml").read_text(encoding="utf-8")
    assert "Verify invalid QR output path fails closed" in playbook
    assert "qr_invalid_path_rejected" in playbook
    assert "qr_symlink_rejected" in playbook
    assert "Verify existing QR symlink fails closed" in playbook
    assert "no_log: true" in playbook
    assert "Reject an unexpected invalid-path success" not in playbook


def test_qr_uses_secure_unique_temporary_files_and_atomic_install():
    tasks = load_tasks(QR_TASKS)
    serialized = yaml.safe_dump(tasks)
    install = task_named(tasks, "Install generated QR codes atomically")

    assert "ansible.builtin.tempfile" in serialized
    assert "state: touch" not in serialized
    assert "wireguard_qr_job.path" in serialized
    assert "os.link" in install["ansible.builtin.command"]["argv"][2]


def test_temporary_qr_files_are_removed_even_when_generation_fails():
    tasks = load_tasks(QR_TASKS)
    generation_block = task_named(tasks, "Generate and install QR codes safely")

    assert "block" in generation_block
    assert "always" in generation_block
    assert any(task.get("name") == "Remove temporary QR files" for task in generation_block["always"])


def test_concurrent_qr_generation_installs_with_atomic_no_replace():
    tasks = load_tasks(QR_TASKS)
    generate = task_named(tasks, "Generate QR codes")
    install = task_named(tasks, "Install generated QR codes atomically")

    assert "creates" not in generate["command"]
    assert generate["changed_when"] is True
    argv = install["ansible.builtin.command"]["argv"]
    assert argv[0] == "{{ ansible_playbook_python }}"
    assert "os.link" in argv[2]
    assert "follow_symlinks=False" in argv[2]
    assert argv[3:] == [
        "{{ wireguard_qr_job.path }}",
        "{{ wireguard_config_path }}/{{ wireguard_qr_job.item }}.png",
    ]


def test_atomic_qr_installer_never_replaces_an_existing_destination(tmp_path):
    tasks = load_tasks(QR_TASKS)
    install = task_named(tasks, "Install generated QR codes atomically")
    code = install["ansible.builtin.command"]["argv"][2]
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    destination = tmp_path / "client.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    subprocess.run([sys.executable, "-c", code, str(first), str(destination)], check=True)
    collision = subprocess.run(
        [sys.executable, "-c", code, str(second), str(destination)], capture_output=True, check=False
    )

    assert collision.returncode != 0
    assert destination.read_bytes() == b"first"


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
    assert any(task.get("name") == "Release QR generation lock safely" for task in locked["always"])


def test_qr_lock_release_is_guarded_and_bound_to_the_acquired_instance():
    tasks = load_tasks(QR_TASKS)
    acquire = task_named(tasks, "Acquire QR generation lock atomically")
    release = task_named(tasks, "Release QR generation lock safely")
    acquire_argv = acquire["ansible.builtin.command"]["argv"]
    release_argv = release["ansible.builtin.command"]["argv"]

    assert acquire["register"] == "wireguard_qr_lock"
    assert "secrets.token_hex" in acquire_argv[2]
    assert "st_ino" in acquire_argv[2]
    assert release_argv[0:2] == ["{{ ansible_playbook_python }}", "-c"]
    assert "fcntl.flock" in release_argv[2]
    assert "st_ino" in release_argv[2]
    assert "owner" in release_argv[2]
    assert release_argv[3:] == [
        "{{ wireguard_config_path }}/.algo-qr.lock",
        "{{ wireguard_config_path }}/.algo-qr-recovery.lock",
        "{{ wireguard_qr_lock.stdout }}",
    ]
    assert release["no_log"] is True


def test_stale_owner_cannot_release_a_successor_lock(tmp_path):
    tasks = load_tasks(QR_TASKS)
    acquire = task_named(tasks, "Acquire QR generation lock atomically")
    release = task_named(tasks, "Release QR generation lock safely")
    acquire_code = acquire["ansible.builtin.command"]["argv"][2]
    release_code = release["ansible.builtin.command"]["argv"][2]
    primary = tmp_path / "primary.lock"
    guard = tmp_path / "guard.lock"

    first = subprocess.run(
        [sys.executable, "-c", acquire_code, str(primary), str(guard), "1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    old = primary.stat().st_mtime - 2
    os.utime(primary, (old, old))
    second = subprocess.run(
        [sys.executable, "-c", acquire_code, str(primary), str(guard), "1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    subprocess.run([sys.executable, "-c", release_code, str(primary), str(guard), first], check=True)
    assert primary.is_dir()
    subprocess.run([sys.executable, "-c", release_code, str(primary), str(guard), second], check=True)
    assert not primary.exists()


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
