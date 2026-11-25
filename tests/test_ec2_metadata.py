"""Check the bootstrap's EC2 HTTP request sequence without contacting metadata."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("token_status", "public_ip", "expected_requests"),
    [
        ("200", True, ["token", "public-v2"]),
        ("200", False, ["token", "public-v2", "public-v2"]),
        ("200-empty", False, ["token"]),
        ("200-multiline", False, ["token"]),
        ("404", True, ["token", "domain", "public-v1"]),
        ("405", True, ["token", "domain", "public-v1"]),
        ("404", False, ["token", "domain", "public-v1", "public-v1"]),
        ("404-other", False, ["token", "domain"]),
        ("401", False, ["token"]),
        ("403", False, ["token"]),
        ("500", False, ["token"]),
        ("timeout", False, ["token"]),
    ],
)
def test_ec2_public_endpoint(tmp_path: Path, token_status: str, public_ip: bool, expected_requests: list[str]) -> None:
    curl = tmp_path / "curl"
    curl.write_text(r"""#!/bin/bash
case "${!#}" in
  */api/token)
    echo token >> "$REQUESTS"
    [[ " $* " == *' -X PUT '* && " $* " == *'X-aws-ec2-metadata-token-ttl-seconds: 60'* ]] || exit 22
    case "$TOKEN_STATUS" in
      200) printf test-metadata-token ;;
      200-multiline) printf 'bad\ntoken' ;;
      timeout) exit 28 ;;
    esac
    [[ " $* " == *'%{http_code}'* ]] && printf '\n%s' "${TOKEN_STATUS%%-*}"
    ;;
  */meta-data/services/domain)
    echo domain >> "$REQUESTS"
    if [[ "$TOKEN_STATUS" == 404-other ]]; then
      echo example.invalid
    else
      echo amazonaws.com
    fi ;;
  */meta-data/public-ipv4)
    if [[ " $* " == *'X-aws-ec2-metadata-token: test-metadata-token'* ]]; then
      echo public-v2 >> "$REQUESTS"
    elif [[ " $* " != *' -H '* ]]; then
      echo public-v1 >> "$REQUESTS"
    else
      exit 22
    fi
    [[ "$PUBLIC_IP" == yes ]] || exit 22
    echo 203.0.113.8 ;;
  *) exit 22 ;;
esac
""")
    curl.chmod(0o755)
    for name, body in [("cat", "echo 'Amazon EC2'"), ("sleep", "exit 0")]:
        command = tmp_path / name
        command.write_text(f"#!/bin/sh\n{body}\n")
        command.chmod(0o755)
    requests = tmp_path / "requests"
    env = {
        **os.environ,
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "TOKEN_STATUS": token_status,
        "PUBLIC_IP": "yes" if public_ip else "no",
        "REQUESTS": str(requests),
    }
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; publicIpFromMetadata', "bootstrap", str(ROOT / "install.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=12,
    )
    assert (result.returncode == 0) == public_ip, result.stderr
    assert ("203.0.113.8" in result.stdout) == public_ip
    assert requests.read_text().splitlines() == expected_requests
    assert "test-metadata-token" not in result.stdout + result.stderr
    if not public_ip:
        assert "Supply the public VPN endpoint" in result.stderr


@pytest.mark.parametrize("piped", [False, True], ids=["file", "stdin"])
def test_bootstrap_reaches_package_install(tmp_path: Path, piped: bool) -> None:
    """Exercise both documented launch methods, stopping at the package manager."""
    installer = ROOT / "install.sh"
    apt = tmp_path / "apt-get"
    apt.write_text('#!/bin/sh\n[ "$1" = update ] || exit 1\nexit 73\n')
    apt.chmod(0o755)
    result = subprocess.run(
        ["bash", "-s" if piped else str(installer)],
        input=installer.read_bytes() if piped else None,
        env={**os.environ, "METHOD": "local", "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        capture_output=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 73, result.stderr.decode()
