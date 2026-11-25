"""Run the container entrypoint against two temporary config stores and the real rsync."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def wrapper(tmp_path):
    mount = tmp_path / "data"
    runtime = tmp_path / "runtime"
    store = mount / "configs"
    store.mkdir(parents=True)
    (runtime / "configs").mkdir(parents=True)
    (mount / "config.cfg").write_bytes(b"users: [phone]\r\n")
    script = tmp_path / "entrypoint"
    script.write_text(
        (ROOT / "algo-docker.sh")
        .read_text()
        .replace('ALGO_DIR="/algo"', f'ALGO_DIR="{runtime}"')
        .replace('DATA_DIR="/data"', f'DATA_DIR="{mount}"')
        .replace("/dev/console", str(mount / "config.cfg"))
    )
    launcher = runtime / "algo"
    launcher.write_text('#!/bin/sh\ntest -L "$(dirname "$0")/configs/localhost"\n')
    launcher.chmod(0o700)
    return mount, runtime, script


def invoke(script, **environment):
    return subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        timeout=20,
        env={**os.environ, **environment},
        check=False,
    )


@pytest.mark.parametrize("portable", [False, True])
def test_localhost_round_trip(tmp_path, portable):
    mount, runtime, script = wrapper(tmp_path)
    config = mount / "configs/vpn"
    config.mkdir()
    (config / ".config.yml").write_text("server: localhost\n")
    alias = mount / "configs/localhost"
    if portable:
        (mount / ".algo-localhost").write_text("vpn\n")
        binary = tmp_path / "bin"
        binary.mkdir()
        link = binary / "ln"
        link.write_text(f'#!/bin/sh\n[ "$3" != "{alias}" ] || exit 1\nexec {shutil.which("ln")} "$@"\n')
        link.chmod(0o700)
        environment = {"PATH": f"{binary}:{os.environ['PATH']}"}
    else:
        alias.symlink_to("vpn")
        environment = {}
    for _ in range(2):
        result = invoke(script, **environment)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (runtime / "configs/localhost").readlink() == Path("vpn")
        assert (mount / ".algo-localhost").read_text() == "vpn\n"
    assert alias.is_symlink() != portable
    assert (runtime / "config.cfg").read_bytes() == b"users: [phone]\n"


@pytest.mark.parametrize("problem", ["outside", "duplicate", "blank-marker"])
def test_ambiguous_inputs_preserve_host_store(tmp_path, problem):
    mount, runtime, script = wrapper(tmp_path)
    store = mount / "configs"
    (store / "vpn").mkdir()
    (store / "vpn/.config.yml").write_text("one")
    if problem == "outside":
        (store / "foreign").symlink_to(tmp_path)
    elif problem == "duplicate":
        (store / "localhost").mkdir()
        (store / "localhost/.config.yml").write_text("different")
    else:
        (mount / ".algo-localhost").write_text("\n")
    result = invoke(script)
    assert result.returncode != 0
    assert not (runtime / "configs/vpn").exists()
    assert (store / "vpn/.config.yml").read_text() == "one"
