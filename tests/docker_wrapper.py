"""Verify Docker config persistence with a disposable deployment process."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def check_config_persistence(
    image: str,
    deployment_status: int,
    *,
    read_only: bool = False,
) -> None:
    """Check that deployment failures preserve configs and copy failures fail.

    Args:
        image: Locally built Algo image to test.
        deployment_status: Exit status returned by the deployment stub.
        read_only: Make the data mount read-only to simulate a copy failure.
    """
    root = Path(__file__).resolve().parents[1]
    with TemporaryDirectory(prefix=".docker-wrapper-", dir=root.parent) as directory:
        temporary = Path(directory)
        data = temporary / "data"
        data.mkdir()
        (data / "config.cfg").write_text("users: [test-user]\n")
        launcher = temporary / "algo"
        launcher.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            "printf 'generated config\\n' > /algo/configs/regression-result\n"
            f"exit {deployment_status}\n"
        )
        launcher.chmod(0o755)
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-t",
                "--cap-drop=all",
                "--entrypoint",
                "/bin/bash",
                "--mount",
                f"type=bind,source={data},target=/data" + (",readonly" if read_only else ""),
                "--mount",
                f"type=bind,source={launcher},target=/algo/algo,readonly",
                "--mount",
                f"type=bind,source={root / 'algo-docker.sh'},target=/algo/algo-docker.sh,readonly",
                image,
                "/algo/algo-docker.sh",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if read_only:
            assert result.returncode != 0, result.stdout + result.stderr
        else:
            assert result.returncode == deployment_status, result.stdout + result.stderr
            assert (data / "configs/regression-result").read_text() == "generated config\n"


def check_bootstrap_failure(image: str, *, existing_log: bool) -> None:
    """Check bootstrap arguments, private log permissions, and failure propagation.

    Args:
        image: Locally built Algo image with Bash and core Unix commands.
        existing_log: Start with a readable log from an earlier installation.
    """
    root = Path(__file__).resolve().parents[1]
    with TemporaryDirectory(prefix=".docker-bootstrap-", dir=root.parent) as directory:
        temporary = Path(directory)
        commands = temporary / "bin"
        commands.mkdir()
        logs = temporary / "logs"
        logs.mkdir()
        if existing_log:
            log = logs / "algo.log"
            log.write_text("previous deployment\n")
            log.chmod(0o644)
        for name, body in {
            "apt-get": "printf '%s\\n' \"$@\" >> /test/packages\n",
            "curl": "exit 0\n",
            "git": "printf '%s\\n' \"$@\" > /test/git-args\nmkdir -p /opt/algo\n",
            "jq": "printf '[\"user1\"]\\n'\n",
            "uv": (
                "if [[ $1 == run ]]; then\n"
                "  printf '%s\\n' \"$@\" > /test/uv-args\n"
                "  echo 'deployment failed'\n"
                "  exit 23\n"
                "fi\n"
            ),
        }.items():
            command = commands / name
            command.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body)
            command.chmod(0o755)
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "/bin/bash",
                "--env",
                "PATH=/test/bin:/usr/local/bin:/usr/bin:/bin",
                "--mount",
                f"type=bind,source={temporary},target=/test",
                "--mount",
                f"type=bind,source={logs},target=/var/log",
                "--mount",
                f"type=bind,source={root / 'install.sh'},target=/test/install.sh,readonly",
                image,
                "/test/install.sh",
                "local",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 23, result.stdout + result.stderr
        assert "main" in (temporary / "git-args").read_text().splitlines()
        assert "git" in (temporary / "packages").read_text().splitlines()
        assert "local_install_confirmed=true" in (temporary / "uv-args").read_text()
        assert (logs / "algo.log").stat().st_mode & 0o077 == 0


if __name__ == "__main__":
    check_config_persistence(sys.argv[1], 0)
    check_config_persistence(sys.argv[1], 23)
    check_config_persistence(sys.argv[1], 0, read_only=True)
    check_bootstrap_failure(sys.argv[1], existing_log=False)
    check_bootstrap_failure(sys.argv[1], existing_log=True)
