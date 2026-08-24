"""Regression tests for release and installer branch paths."""

import re
import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
SHA256 = re.compile(r"[0-9a-f]{64}")


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

    push = workflow["on"]["push"]
    assert push["branches"] == ["main"]
    assert push["tags"] == ["v*.*.*"]

    metadata_steps = [step for step in workflow["jobs"]["build-and-push-image"]["steps"] if step.get("id") == "meta"]
    assert len(metadata_steps) == 1

    active_tag_rules = [
        line.strip()
        for line in metadata_steps[0]["with"]["tags"].splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active_tag_rules == [
        "type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}",
        "type=semver,pattern={{version}}",
        "type=semver,pattern={{major}}.{{minor}}",
    ]

    active_labels = [
        line.strip()
        for line in metadata_steps[0]["with"]["labels"].splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active_labels == [
        "org.opencontainers.image.created={{commit_date 'YYYY-MM-DDTHH:mm:ss.SSS[Z]'}}",
        "org.opencontainers.image.revision=${{ github.sha }}",
        "org.opencontainers.image.version=${{ github.ref_name }}",
    ]

    build_steps = [
        step
        for step in workflow["jobs"]["build-and-push-image"]["steps"]
        if step.get("uses", "").startswith("docker/build-push-action@")
    ]
    assert len(build_steps) == 1
    assert build_steps[0]["with"]["labels"] == "${{ steps.meta.outputs.labels }}"


def test_actionlint_checks_yml_and_yaml_workflows():
    workflow = yaml.safe_load((ROOT / ".github/workflows/lint.yml").read_text())
    actionlint_steps = [
        step for step in workflow["jobs"]["actionlint"]["steps"] if step.get("name") == "Run actionlint"
    ]

    assert len(actionlint_steps) == 1
    commands = [line.strip() for line in actionlint_steps[0]["run"].splitlines() if line.strip()]
    assert commands == ["actionlint .github/workflows/*.yml .github/workflows/*.yaml"]


def test_dockerfile_uses_versioned_digest_pinned_sources():
    text = (ROOT / "Dockerfile").read_text()

    assert re.search(r"^FROM python:3\.12-alpine@sha256:[0-9a-f]{64}$", text, re.MULTILINE)
    assert re.search(
        r"^COPY --from=ghcr\.io/astral-sh/uv:0\.12\.3@sha256:[0-9a-f]{64} /uv /bin/uv$",
        text,
        re.MULTILINE,
    )
    assert "ghcr.io/astral-sh/uv:latest" not in text


def test_uv_download_fallbacks_are_versioned_and_checksum_verified():
    installer = (ROOT / "install.sh").read_text()
    launcher = (ROOT / "algo").read_text()

    for text in (installer, launcher):
        assert 'UV_VERSION="0.12.3"' in text
        checksum = re.search(r'^UV_INSTALLER_SHA256="([0-9a-f]{64})"$', text, re.MULTILINE)
        assert checksum and SHA256.fullmatch(checksum.group(1))
        assert "verify_sha256" in text
        assert not re.search(r"https?://[^\n|]+\|\s*(?:sh|bash|iex)\b", text)

    powershell_checksum = re.search(r'^UV_INSTALLER_PS1_SHA256="([0-9a-f]{64})"$', launcher, re.MULTILINE)
    assert powershell_checksum and SHA256.fullmatch(powershell_checksum.group(1))

    package_manager_call = launcher.index("install_uv_via_package_manager")
    download_call = launcher.index("install_uv_via_download")
    assert package_manager_call < download_call


def test_ci_tool_installers_are_versioned_and_checksum_verified():
    setup_action = yaml.safe_load((ROOT / ".github/actions/setup-uv/action.yml").read_text())
    setup_step = next(step for step in setup_action["runs"]["steps"] if step.get("id") == "setup")
    assert setup_step["with"]["version"] == "0.12.3"

    integration = yaml.safe_load((ROOT / ".github/workflows/integration-tests.yml").read_text())
    integration_steps = integration["jobs"]["localhost-deployment"]["steps"]
    assert any(step.get("uses") == "./.github/actions/setup-uv" for step in integration_steps)
    assert "astral.sh/uv/install.sh" not in (ROOT / ".github/workflows/integration-tests.yml").read_text()

    lint_path = ROOT / ".github/workflows/lint.yml"
    lint_text = lint_path.read_text()
    lint = yaml.safe_load(lint_text)
    expected_versions = {
        "ACTIONLINT_VERSION": "1.7.12",
        "POWERSHELL_VERSION": "7.4.0",
        "PSSCRIPTANALYZER_VERSION": "1.25.0",
    }
    for name, version in expected_versions.items():
        assert lint["env"][name] == version
    assert SHA256.fullmatch(lint["env"]["ACTIONLINT_SHA256"])
    assert SHA256.fullmatch(lint["env"]["POWERSHELL_DEB_SHA256"])
    assert SHA256.fullmatch(lint["env"]["PSSCRIPTANALYZER_SHA256"])
    assert "rhysd/actionlint/main" not in lint_text
    assert "sha256sum --check" in lint_text
    assert "PowerShell/PSScriptAnalyzer/releases/download" in lint_text
    assert "Install-Module" not in lint_text


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
