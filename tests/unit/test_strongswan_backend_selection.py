"""OS-driven StrongSwan backend selection and lifecycle contract."""

from pathlib import Path

import yaml


def test_swanctl_native_harness_recreates_role_runtime_prerequisites():
    harness = Path("tests/integration/test-strongswan-swanctl.sh").read_text(encoding="utf-8")

    assert "install -d -m 0755 /var/lib/strongswan" in harness
    assert harness.index("install -d -m 0755 /var/lib/strongswan") < harness.index("systemctl restart strongswan")
    assert "journalctl -b --no-pager -u strongswan.service" in harness


def test_supported_ubuntu_facts_select_starter_for_2204_and_swanctl_for_2404():
    facts = Path("roles/common/tasks/facts.yml").read_text(encoding="utf-8")

    assert "is_ubuntu_22" in facts
    assert "is_ubuntu_24" in facts
    assert "strongswan_backend" in facts
    assert "'swanctl' if is_ubuntu_24 else 'starter'" in facts


def test_backend_controls_service_and_packages_without_version_guessing():
    defaults = Path("roles/strongswan/defaults/main.yml").read_text(encoding="utf-8")
    ubuntu = Path("roles/strongswan/tasks/ubuntu.yml").read_text(encoding="utf-8")

    assert (
        "strongswan_service: \"{{ 'strongswan-starter' if strongswan_backend == 'starter' else 'strongswan' }}\""
        in defaults
    )
    assert "distribution_version" not in defaults.split("strongswan_service:", 1)[1].splitlines()[0]
    assert "charon-systemd" in ubuntu
    assert "strongswan-swanctl" in ubuntu
    assert "strongswan_backend == 'swanctl'" in ubuntu
    assert "strongswan_backend == 'starter'" in ubuntu


def test_backend_specific_reload_is_explicit_and_secret_safe():
    handlers = yaml.safe_load(Path("roles/strongswan/handlers/main.yml").read_text(encoding="utf-8"))
    names = {handler["name"]: handler for handler in handlers}

    swanctl_reload = names["reload swanctl configuration"]
    assert swanctl_reload["command"] == "swanctl --load-all --noprompt"
    assert swanctl_reload["when"] == "strongswan_backend == 'swanctl'"
    assert swanctl_reload["no_log"] is True

    crl_reload = names["rereadcrls"]
    assert "swanctl --load-authorities --noprompt" in crl_reload["shell"]
    assert "ipsec rereadcrls" in crl_reload["shell"]
