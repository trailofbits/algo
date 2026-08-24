"""Regression tests for release and installer branch paths."""

import re
import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]


def test_installer_defaults_to_main():
    text = (ROOT / "install.sh").read_text()
    clone_commands = [line for line in text.splitlines() if re.search(r"\bgit\s+clone\b", line)]

    assert text.count("REPO_BRANCH=") == 1
    assert 'REPO_BRANCH="${REPO_BRANCH:-main}"' in text
    assert len(clone_commands) == 1
    assert "${REPO_BRANCH}" in clone_commands[0]
    assert "master" not in text
    assert "--branch master" not in text
    assert "-b master" not in text


def test_docker_workflow_publishes_from_main():
    workflow = yaml.safe_load((ROOT / ".github/workflows/docker-image.yaml").read_text())

    assert workflow["on"]["push"]["branches"] == ["main"]

    metadata_steps = [step for step in workflow["jobs"]["build-and-push-image"]["steps"] if step.get("id") == "meta"]
    assert len(metadata_steps) == 1

    active_tag_rules = [
        line.strip()
        for line in metadata_steps[0]["with"]["tags"].splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active_tag_rules == ["type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}"]


def test_installer_documentation_does_not_use_positional_arguments():
    text = (ROOT / "docs/deploy-from-script-or-cloud-init-to-localhost.md").read_text()
    bash_invocations = []
    for line in text.splitlines():
        if "|" not in line or "bash" not in line:
            continue
        command = shlex.split(line)
        bash_index = command.index("bash")
        bash_invocations.append(command[bash_index + 1 :])

    assert bash_invocations
    assert "bash -x -s" not in text
    assert "bash -s --" not in text
    for arguments in bash_invocations:
        assert all(argument.startswith("-") for argument in arguments)
        assert not any(
            argument.startswith("-") and not argument.startswith("--") and "s" in argument[1:] for argument in arguments
        )
    assert "REPO_BRANCH=main" in text
