"""Check the bootstrap's EC2 HTTP request sequence without contacting metadata."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("available", [True, False])
def test_ec2_public_endpoint(tmp_path, available):
    curl = tmp_path / "curl"
    curl.write_text("""#!/bin/bash
case "${!#}" in
  */api/token)
    [[ " $* " == *' -X PUT '* && " $* " == *'X-aws-ec2-metadata-token-ttl-seconds: 60'* ]] || exit 22
    echo test-metadata-token ;;
  */meta-data/public-ipv4)
    [[ " $* " == *'X-aws-ec2-metadata-token: test-metadata-token'* && "$PUBLIC_IP" == yes ]] || exit 22
    echo 203.0.113.8 ;;
  *) exit 22 ;;
esac
""")
    curl.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}", "PUBLIC_IP": "yes" if available else "no"}
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; publicIpFromMetadata', "bootstrap", str(ROOT / "install.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=12,
    )
    assert (result.returncode == 0) == available
    assert ("203.0.113.8" in result.stdout) == available
    assert "test-metadata-token" not in result.stdout + result.stderr
    if not available:
        assert "Supply the public VPN endpoint" in result.stderr
