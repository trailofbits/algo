"""Check blocklist refresh behavior at the download and service boundaries."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from ansible.plugins.filter.core import FilterModule
from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def adblock(tmp_path: Path):
    config = tmp_path / "etc" / "dnscrypt-proxy"
    config.mkdir(parents=True)
    (config / "blacklist.txt").write_text("previous.example\n")
    commands = tmp_path / "bin"
    commands.mkdir()
    for name, body in {
        "wget": (
            "print(os.environ.get('HOSTS', '0.0.0.0 ads.example\\n127.0.0.1 localhost'))\n"
            "sys.exit(int(os.environ.get('DOWNLOAD_STATUS', '0')))\n"
        ),
        "systemctl": "\n".join(
            [
                "Path(os.environ['RESTARTED']).touch()",
                "sys.exit(int(os.getenv('RESTART_STATUS', '0')))",
            ]
        ),
    }.items():
        executable = commands / name
        header = f"#!{sys.executable}\nimport os, sys\nfrom pathlib import Path\n"
        executable.write_text(header + body)
        executable.chmod(0o700)
    environment = Environment(undefined=StrictUndefined)
    environment.filters.update(FilterModule().filters())
    template = environment.from_string((ROOT / "roles/dns/templates/adblock.sh.j2").read_text())
    script = tmp_path / "adblock.sh"
    content = template.render(
        config_prefix=f"{tmp_path}/",
        adblock_lists=["https://example.test/hosts"],
    )
    script.write_text(content)
    return script, config


def refresh(script: Path, **environment):
    return subprocess.run(
        ["/bin/bash", str(script)],
        env={
            **os.environ,
            "PATH": f"{script.parent / 'bin'}:{os.environ['PATH']}",
            "RESTARTED": str(script.parent / "restarted"),
            **environment,
        },
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


def test_failed_download_preserves_previous_blocklist(adblock):
    script, config = adblock
    result = refresh(script, DOWNLOAD_STATUS="42")
    assert result.returncode != 0
    assert (config / "blacklist.txt").read_text() == "previous.example\n"
    assert not (script.parent / "restarted").exists()
    assert "example.test/hosts" in result.stderr


def test_success_applies_local_lists_and_cleans_temporary_files(adblock):
    script, config = adblock
    (config / "black.list").write_text("extra.example\n")
    (config / "white.list").write_text("ads.example\n")
    result = refresh(script)
    assert result.returncode == 0, result.stderr
    assert (config / "blacklist.txt").read_text() == "extra.example\n"
    assert (config / "blacklist.txt").stat().st_mode & 0o777 == 0o644
    assert (script.parent / "restarted").exists()
    assert not list(config.glob(".adblock.*"))


def test_whitelist_can_remove_every_entry(adblock):
    script, config = adblock
    (config / "white.list").write_text("ads.example\n")
    result = refresh(script)
    assert result.returncode == 0, result.stderr
    assert (config / "blacklist.txt").read_text() == ""


def test_restart_failure_is_reported(adblock):
    script, _ = adblock
    result = refresh(script, RESTART_STATUS="23")
    assert result.returncode != 0


def test_invalid_whitelist_preserves_previous_blocklist(adblock):
    script, config = adblock
    (config / "white.list").write_text("[\n")
    result = refresh(script)
    assert result.returncode != 0
    assert (config / "blacklist.txt").read_text() == "previous.example\n"
    assert not (script.parent / "restarted").exists()
    assert "Failed to filter" in result.stderr
