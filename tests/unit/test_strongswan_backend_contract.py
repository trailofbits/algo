"""Semantic parity contract for the starter and swanctl server backends."""

import re
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATE_DIR = Path("roles/strongswan/templates")
ROLE_DIR = Path("roles/strongswan")

VARS = {
    "IP_subject_alt_name": "vpn.example.test",
    "strongswan_log_level": "-1",
    "strongswan_network": "10.48.0.0/16",
    "strongswan_network_ipv6": "2001:db8:4160::/48",
    "local_service_ip": "172.16.0.10",
    "local_service_ipv6": "fd00::10",
    "ipv6_support": True,
    "algo_dns_adblocking": False,
    "dns_encryption": True,
    "dns_servers": {
        "ipv4": ["1.1.1.1", "1.0.0.1"],
        "ipv6": ["2606:4700:4700::1111", "2606:4700:4700::1001"],
    },
    "ciphers": {
        "defaults": {
            "ike": "aes256gcm16-prfsha512-ecp384!",
            "esp": "aes256gcm16-ecp384!",
        }
    },
}


def render(name: str) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), undefined=StrictUndefined)
    env.filters["bool"] = bool
    return env.get_template(name).render(**VARS)


def assert_secure_crypto(config: str) -> None:
    lowered = config.lower()
    assert "aes256gcm16-prfsha512-ecp384" in lowered
    assert "aes256gcm16-ecp384" in lowered
    weak = re.compile(r"(?<![a-z0-9])(3des|des|md5|sha1|modp768|modp1024)(?![a-z0-9])")
    match = weak.search(lowered)
    assert match is None, f"weak algorithm in configuration: {match.group(0) if match else ''}"


def test_starter_and_swanctl_share_secure_crypto_and_authentication_contract():
    starter = render("ipsec.conf.j2")
    swanctl = render("swanctl.conf.j2")

    for config in (starter, swanctl):
        assert_secure_crypto(config)
        assert "vpn.example.test" in config
        assert "vpn.example.test.crt" in config
        assert config.lower().count("pubkey") >= 2
        assert "0.0.0.0/0" in config
        assert "::/0" in config


def test_starter_and_swanctl_share_pool_and_dns_contract():
    starter = render("ipsec.conf.j2")
    swanctl = render("swanctl.conf.j2")

    for config in (starter, swanctl):
        assert "10.48.0.0/16" in config
        assert "2001:db8:4160::/48" in config
        assert "172.16.0.10" in config
        assert "fd00::10" in config


def test_certificate_identity_constraints_and_strict_revocation_match():
    starter = render("ipsec.conf.j2")
    swanctl = render("swanctl.conf.j2")
    openssl = (ROLE_DIR / "tasks/openssl.yml").read_text(encoding="utf-8")

    assert "strictcrlpolicy=yes" in starter
    assert "revocation = strict" in swanctl
    assert 'common_name: "{{ item }}"' in openssl
    assert "email:{{ item }}@{{ openssl_constraint_random_id }}" in openssl
    assert "clientAuth" in openssl
    assert "serverAuth" in openssl
    assert 'loop: "{{ users }}"' in openssl


def test_logging_privacy_and_firewall_contract_is_backend_independent():
    starter = render("ipsec.conf.j2")
    strongswan = render("strongswan.conf.j2")
    rules_v4 = (ROLE_DIR.parent / "common/templates/rules.v4.j2").read_text(encoding="utf-8")
    rules_v6 = (ROLE_DIR.parent / "common/templates/rules.v6.j2").read_text(encoding="utf-8")

    assert 'charondebug="ike -1' in starter
    assert "charon-systemd" in strongswan
    assert "default = -1" in strongswan
    for rules in (rules_v4, rules_v6):
        assert "strongswan_backend" not in rules
        assert "500" in rules and "4500" in rules
        assert "esp" in rules and "ah" in rules


def test_backend_file_contract_keeps_crls_and_private_keys_secure():
    configuration = yaml.safe_load((ROLE_DIR / "tasks/ipsec_configuration.yml").read_text(encoding="utf-8"))
    distribution = yaml.safe_load((ROLE_DIR / "tasks/distribute_keys.yml").read_text(encoding="utf-8"))
    openssl = yaml.safe_load((ROLE_DIR / "tasks/openssl.yml").read_text(encoding="utf-8"))

    swanctl_config = next(task for task in configuration if task.get("name") == "Setup secure swanctl configuration")
    assert swanctl_config["template"] == {
        "src": "swanctl.conf.j2",
        "dest": "{{ config_prefix | default('/') }}etc/swanctl/swanctl.conf",
        "owner": "root",
        "group": "{{ root_group | default('root') }}",
        "mode": "0600",
    }
    assert swanctl_config["when"] == "strongswan_backend == 'swanctl'"

    swanctl_keys = next(
        task for task in distribution if task.get("name") == "Copy the keys to the swanctl credential directories"
    )
    assert swanctl_keys["copy"]["dest"] == "{{ config_prefix | default('/') }}etc/swanctl/{{ item.dest }}"
    assert swanctl_keys["copy"]["owner"] == "strongswan"
    assert swanctl_keys["copy"]["mode"] == "0600"
    assert {item["dest"] for item in swanctl_keys["loop"]} == {
        "x509ca/ca.crt",
        "x509/{{ IP_subject_alt_name }}.crt",
        "private/{{ IP_subject_alt_name }}.key",
    }
    assert swanctl_keys["when"] == "strongswan_backend == 'swanctl'"

    swanctl_crl = next(
        task for task in openssl if task.get("name") == "Copy the CRL to the swanctl credential directory"
    )
    assert swanctl_crl["copy"]["dest"] == "{{ config_prefix | default('/') }}etc/swanctl/x509crl/algo.root.pem"
    assert swanctl_crl["copy"]["mode"] == "0644"
    assert swanctl_crl["when"] == "strongswan_backend == 'swanctl'"


def test_swanctl_plugins_and_reload_commands_do_not_depend_on_stroke():
    defaults = (ROLE_DIR / "defaults/main.yml").read_text(encoding="utf-8")
    handlers = (ROLE_DIR / "handlers/main.yml").read_text(encoding="utf-8")

    assert "  - vici" in defaults
    assert "swanctl --load-all --noprompt" in handlers
    assert "swanctl --load-authorities --noprompt" in handlers
    assert "ipsec rereadcrls" in handlers  # starter remains supported on 22.04
