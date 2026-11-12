"""Check the service sandbox required by StrongSwan's control and kernel sockets."""

import configparser
from pathlib import Path

import pytest
from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "roles/strongswan/templates/100-CustomLimitations.conf.j2"


@pytest.fixture
def service_settings() -> configparser.SectionProxy:
    """Render the production drop-in and parse its systemd service settings."""
    rendered = Environment(undefined=StrictUndefined).from_string(TEMPLATE.read_text()).render()
    settings = configparser.ConfigParser(interpolation=None, strict=False)
    settings.read_string(rendered)
    return settings["Service"]


def test_procfs_socket_table_is_not_a_bind_mount(
    service_settings: configparser.SectionProxy,
) -> None:
    """The process-relative PF_KEY table must not become a namespace mount target."""
    paths = service_settings.get("ReadOnlyPaths", "").split()
    assert "/proc/net/pfkey" not in {path.lstrip("-+") for path in paths}


def test_kernel_and_control_sockets_are_allowed(
    service_settings: configparser.SectionProxy,
) -> None:
    """Keep IPsec transport, Linux XFRM, and the local stroke control socket available."""
    families = service_settings["RestrictAddressFamilies"].split()
    assert {"AF_INET", "AF_INET6", "AF_NETLINK", "AF_UNIX"}.issubset(families)


@pytest.mark.parametrize(
    "setting",
    [
        "NoNewPrivileges",
        "ProtectHome",
        "PrivateTmp",
        "ProtectKernelTunables",
        "ProtectControlGroups",
    ],
)
def test_preserves_hardening(service_settings: configparser.SectionProxy, setting: str) -> None:
    """Keep the protections that do not depend on a process-relative procfs path."""
    assert service_settings.getboolean(setting)
