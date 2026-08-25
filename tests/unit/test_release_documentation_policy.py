"""Release metadata, support scope, and documentation link policy."""

import re
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[2]
AZURE_EXCLUSION_PAGE = """# Microsoft Azure (excluded)

Microsoft Azure is **excluded and unverified** in this release. The Azure provider is rejected before provisioning, so this page intentionally provides no setup, authentication, or deployment instructions.

Use one of the retained providers listed in the [documentation index](index.md), or deploy to an [existing supported Ubuntu server](deploy-to-ubuntu.md). Historical Azure role code or prompts are not a support or security-validation claim.
"""


def _assert_azure_page_is_exclusion_only(text):
    assert text == AZURE_EXCLUSION_PAGE


def test_azure_exclusion_policy_rejects_alternate_onboarding_wording():
    azure = (ROOT / "docs" / "cloud-azure.md").read_text(encoding="utf-8")

    with pytest.raises(AssertionError):
        _assert_azure_page_is_exclusion_only(azure + "\n```bash\naz account show\n```\n")


def test_release_version_and_python_support_are_consistent():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked_algo = next(package for package in lock["package"] if package["name"] == "algo")

    assert project["version"] == locked_algo["version"] == "2.0.0b0"
    assert project["requires-python"] == ">=3.12"

    documentation = [ROOT / "README.md", ROOT / "docs" / "deploy-from-macos.md", ROOT / "docs" / "troubleshooting.md"]
    ci_files = list((ROOT / ".github" / "workflows").glob("*.*ml"))
    ci_files += list((ROOT / ".github" / "actions").glob("*/action.yml"))
    assert not [
        str(path.relative_to(ROOT)) for path in documentation if "Python 3.11" in path.read_text(encoding="utf-8")
    ]
    assert not [
        str(path.relative_to(ROOT))
        for path in ci_files
        if re.search(r"(?:python-version:|default:) ['\"]3\.11['\"]", path.read_text(encoding="utf-8"))
    ]


def test_support_and_promotion_claims_are_bounded_and_current():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    ec2 = (ROOT / "docs" / "cloud-amazon-ec2.md").read_text(encoding="utf-8")

    assert "works on all platforms" not in readme
    assert "Ubuntu and other distributions" not in readme
    assert "promotion offering free t4g.small instances until December 31, 2025" not in ec2
    assert "Ubuntu 22.04 LTS" in readme
    assert "Azure and Amazon Lightsail are currently excluded" in readme


def test_excluded_provider_claims_are_consistent_repository_wide():
    forbidden = (
        "Supported cloud providers: DigitalOcean, AWS, Azure",
        "Deploy on AWS, DigitalOcean, Azure, GCP",
        "Amazon [EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) and [Lightsail]",
        "specific region you want to install to in Microsoft Azure",
    )
    stale = []
    for path in [ROOT / "CONTRIBUTING.md", *sorted((ROOT / "docs").rglob("*.md"))]:
        text = path.read_text(encoding="utf-8")
        if any(claim in text for claim in forbidden):
            stale.append(str(path.relative_to(ROOT)))
    assert not stale, f"contradictory excluded-provider claims: {stale}"
    troubleshooting = (ROOT / "docs" / "troubleshooting.md").read_text(encoding="utf-8")
    index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    azure = (ROOT / "docs" / "cloud-azure.md").read_text(encoding="utf-8")
    assert "cloud-azure" not in troubleshooting
    assert "### Azure:" not in troubleshooting
    assert "Configure [Azure]" not in index
    _assert_azure_page_is_exclusion_only(azure)
    installer_guide = (ROOT / "docs" / "deploy-from-script-or-cloud-init-to-localhost.md").read_text(encoding="utf-8")
    endpoint_guidance = next(line for line in installer_guide.splitlines() if line.startswith("- `ENDPOINT`:"))
    assert "Azure" not in endpoint_guidance


def test_ubuntu_support_and_ec2_selector_docs_match_the_bounded_contract():
    unsupported_cloud = (ROOT / "docs" / "deploy-to-unsupported-cloud.md").read_text(encoding="utf-8")
    troubleshooting = (ROOT / "docs" / "troubleshooting.md").read_text(encoding="utf-8")
    ansible = (ROOT / "docs" / "deploy-from-ansible.md").read_text(encoding="utf-8")

    stale_claims = (
        "Algo exclusively supports Ubuntu 22.04 LTS",
        "Ubuntu 22.04 LTS, the only supported server platform",
        "Algo requires Ubuntu 22.04 LTS",
        'prepends with "ubuntu/images/hvm-ssd/"',
        "Default: Ubuntu latest LTS",
    )
    combined = "\n".join((unsupported_cloud, troubleshooting, ansible))
    assert not [claim for claim in stale_claims if claim in combined]
    assert "Ubuntu 22.04 LTS or Ubuntu 24.04 LTS" in unsupported_cloud
    assert "Ubuntu 22.04 LTS and Ubuntu 24.04 LTS" in troubleshooting
    assert "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04" in ansible
    assert "Azure and Lightsail are excluded and unverified" in ansible


def test_strongswan_diagnostics_cover_both_supported_backends():
    troubleshooting = (ROOT / "docs" / "troubleshooting.md").read_text(encoding="utf-8")
    command_lines = {line.strip() for line in troubleshooting.splitlines()}

    assert "Ubuntu 22.04 (`starter` backend)" in troubleshooting
    assert "systemctl status strongswan-starter" in command_lines
    assert "ipsec statusall                  # Show all IKE_SA and CHILD_SA" in command_lines
    assert "ipsec leases                     # Show assigned virtual IPs" in command_lines
    assert "journalctl -u strongswan-starter -f" in command_lines
    assert "Ubuntu 24.04 (`swanctl` backend)" in troubleshooting
    assert "systemctl status strongswan" in command_lines
    assert "swanctl --list-sas               # Show all IKE_SA and CHILD_SA" in command_lines
    assert "swanctl --list-pools --leases    # Show address-pool usage and assigned leases" in command_lines
    assert "journalctl -u strongswan -f" in command_lines
    assert not [line for line in command_lines if line.startswith("journalctl -t charon")]


def test_repository_documentation_uses_main_branch_links():
    stale = []
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]:
        text = path.read_text(encoding="utf-8")
        if re.search(
            r"github\.com/trailofbits/algo/(?:blob|raw)/master/|github\.com/trailofbits/algo/archive/master", text
        ):
            stale.append(str(path.relative_to(ROOT)))
    assert not stale, f"stale master-branch links: {stale}"


def test_ipsec_checks_are_not_described_as_end_to_end_connectivity():
    workflow = (ROOT / ".github" / "workflows" / "integration-tests.yml").read_text(encoding="utf-8")
    documentation = (ROOT / "tests" / "e2e" / "README.md").read_text(encoding="utf-8")
    script = (ROOT / "tests" / "e2e" / "test-vpn-connectivity.sh").read_text(encoding="utf-8")

    assert "Run E2E VPN connectivity tests" not in workflow
    assert not re.search(r"IPsec.*(?:end-to-end|connectivity)", documentation, re.IGNORECASE)
    assert "true E2E" not in script


def test_internal_link_checker_runs_in_ci_and_reports_no_broken_links():
    checker = ROOT / "scripts" / "check-internal-links.py"
    assert checker.is_file()

    result = subprocess.run([str(checker)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "lint.yml").read_text(encoding="utf-8"))
    commands = "\n".join(step.get("run", "") for job in workflow["jobs"].values() for step in job.get("steps", []))
    assert "scripts/check-internal-links.py" in commands
