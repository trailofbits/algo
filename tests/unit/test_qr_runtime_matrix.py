"""Runtime launcher matrix for secure WireGuard QR generation."""

import os
import shutil
import site
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK = ROOT / "tests/integration/test_qr_generation.yml"
ANSIBLE_PLAYBOOK = Path(sys.executable).with_name("ansible-playbook")


def _run(
    command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _assert_play_passed(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def test_qr_play_runs_with_direct_controller_venv():
    assert ANSIBLE_PLAYBOOK.is_file()
    result = _run([str(ANSIBLE_PLAYBOOK), "-i", "localhost,", str(PLAYBOOK)])
    _assert_play_passed(result)


def test_qr_play_runs_via_uv_from_repository_path_with_spaces(tmp_path):
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is genuinely unavailable")
    assert uv is not None
    spaced_repo = tmp_path / "algo repository path with spaces"
    spaced_repo.symlink_to(ROOT, target_is_directory=True)
    spaced_playbook = spaced_repo / "tests/integration/test_qr_generation.yml"

    result = _run(
        [uv, "run", "--frozen", "ansible-playbook", "-i", "localhost,", str(spaced_playbook)],
        cwd=spaced_repo,
    )
    _assert_play_passed(result)


@pytest.mark.parametrize("segno_state", ["missing", "non-executable"])
def test_qr_preflight_rejects_unusable_segno_at_runtime(tmp_path, segno_state):
    controller_dir = tmp_path / "controller without usable segno"
    controller_dir.mkdir()
    controller_python = controller_dir / "python"
    controller_python.symlink_to(sys.executable)
    if segno_state == "non-executable":
        segno = controller_dir / "segno"
        segno.write_text("not executable", encoding="utf-8")
        segno.chmod(0o600)

    probe = tmp_path / "missing-segno.yml"
    probe.write_text(
        "---\n"
        "- hosts: localhost\n"
        "  connection: local\n"
        "  gather_facts: false\n"
        "  tasks:\n"
        f"    - include_tasks: {ROOT / 'roles/wireguard/tasks/qr.yml'}\n",
        encoding="utf-8",
    )
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(site.getsitepackages()),
    }

    result = _run(
        [str(controller_python), str(ANSIBLE_PLAYBOOK), "-i", "localhost,", str(probe)],
        env=environment,
    )

    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}"
    assert "Segno is not installed as an executable next to ansible_playbook_python" in combined
    assert "uv sync" in combined
