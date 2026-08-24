"""Security documentation policy and local-link checks."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THREAT_MODEL = ROOT / "docs" / "threat-model.md"


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _headings(markdown: str) -> set[str]:
    return {match.group(1).strip().casefold() for match in re.finditer(r"^#{1,6}\s+(.+)$", markdown, re.MULTILINE)}


def _local_links(markdown: str) -> list[str]:
    links = re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", markdown)
    return [link.split("#", 1)[0] for link in links if link and "://" not in link and not link.startswith("#")]


def test_threat_model_records_the_secure_core_policy():
    assert THREAT_MODEL.is_file(), "docs/threat-model.md must define the security boundary"
    threat_model = THREAT_MODEL.read_text(encoding="utf-8")
    headings = _headings(threat_model)

    required_headings = {
        "protected assets and security goals",
        "trust boundaries and assumptions",
        "supply-chain trust",
        "supported secure core",
        "non-goals",
        "feature acceptance gate",
        "rejected feature requests",
    }
    assert required_headings <= headings

    normalized = threat_model.casefold()
    for required_term in (
        "wireguard",
        "ikev2",
        "ubuntu 22.04 lts",
        "digitalocean",
        "amazon ec2",
        "google compute engine",
        "vultr",
        "scaleway",
        "openstack",
        "cloudstack",
        "hetzner",
        "linode",
        "azure",
        "lightsail",
    ):
        assert required_term in normalized
    assert "maintained provisioning scope" in normalized
    assert "credentialed provider canary" in normalized
    assert "#14959" in threat_model and "#14916" in threat_model
    assert re.search(r"azure[^\n]*(excluded|unverified)", normalized)
    assert re.search(r"lightsail[^\n]*(excluded|unverified)", normalized)


def test_security_policy_links_to_the_threat_model_and_states_supported_versions():
    security = _read("SECURITY.md")

    assert "docs/threat-model.md" in security
    assert "## Supported Versions" in security
    assert "2.x" in security
    assert re.search(r"1\.x[^\n]*(no|not|unsupported)", security, re.IGNORECASE)


def test_readme_links_to_secure_core_scope_and_keeps_anti_features_explicit():
    readme = _read("README.md")
    anti_features = readme.split("## Anti-features", 1)[1].split("\n## ", 1)[0].casefold()

    assert "docs/threat-model.md" in readme
    assert "secure core" in readme.casefold()
    for anti_feature in ("xray", "web ui", "anonymity", "censorship"):
        assert anti_feature in anti_features


def test_changed_security_documents_have_no_broken_local_links():
    for relative_path in ("README.md", "SECURITY.md", "docs/threat-model.md"):
        markdown = _read(relative_path)
        base = (ROOT / relative_path).parent
        broken = [link for link in _local_links(markdown) if not (base / link).resolve().exists()]
        assert not broken, f"{relative_path} has broken local links: {broken}"
