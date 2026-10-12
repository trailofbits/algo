"""Regression tests for Ubuntu Pro ESM unattended-upgrade origins (issue #15049)."""

import re
from pathlib import Path

import pytest
from jinja2 import Environment, StrictUndefined

TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "roles"
    / "common"
    / "templates"
    / "50unattended-upgrades.j2"
)


@pytest.mark.parametrize("codename", ["focal", "jammy", "noble"])
def test_unattended_upgrades_allows_ubuntu_pro_security_pockets(codename: str) -> None:
    """Only the Apps and Infra security pockets should be allowed for ESM."""
    rendered = Environment(undefined=StrictUndefined).from_string(
        TEMPLATE.read_text(encoding="utf-8")
    ).render(unattended_reboot={"enabled": False, "time": "03:00"})

    origins_block = rendered.split("Unattended-Upgrade::Allowed-Origins {", 1)[1].split("};", 1)[0]
    origins = {
        origin.replace("${distro_id}", "Ubuntu").replace("${distro_codename}", codename)
        for origin in re.findall(r'^\s*"([^"]+)";', origins_block, flags=re.MULTILINE)
    }

    assert f"Ubuntu:{codename}-security" in origins
    assert f"UbuntuESMApps:{codename}-apps-security" in origins
    assert f"UbuntuESM:{codename}-infra-security" in origins
    assert f"UbuntuESM:{codename}" not in origins
    assert f"UbuntuESMApps:{codename}-apps-updates" not in origins
    assert f"UbuntuESM:{codename}-infra-updates" not in origins
