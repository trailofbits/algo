#!/usr/bin/env python3
"""
Tests for Xray VLESS+Reality VPN role.

These tests verify:
- Template rendering for server and client configs
- VLESS link generation format
- Firewall rules for xray port
- Configuration validation
"""

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Add parent directory to path for fixtures
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fixtures import load_test_variables


def load_template(role, template_name):
    """Load a Jinja2 template from a role's templates directory."""
    template_dir = Path(__file__).parent.parent.parent / "roles" / role / "templates"
    if not template_dir.exists():
        pytest.skip(f"Role {role} templates directory not found")
    env = Environment(loader=FileSystemLoader(str(template_dir)), undefined=StrictUndefined)
    return env.get_template(template_name)


class TestXrayServerConfig:
    """Tests for xray server configuration template."""

    def test_server_config_renders_valid_json(self):
        """Test that server config.json renders as valid JSON."""
        template = load_template("xray", "config.json.j2")
        test_vars = load_test_variables()

        result = template.render(**test_vars)

        # Should be valid JSON
        config = json.loads(result)
        assert isinstance(config, dict)

    def test_server_config_has_vless_inbound(self):
        """Test that server config has VLESS inbound configured."""
        template = load_template("xray", "config.json.j2")
        test_vars = load_test_variables()

        result = template.render(**test_vars)
        config = json.loads(result)

        # Check inbounds
        assert "inbounds" in config
        assert len(config["inbounds"]) > 0

        vless_inbound = config["inbounds"][0]
        assert vless_inbound["protocol"] == "vless"
        assert vless_inbound["port"] == test_vars["xray_port"]

    def test_server_config_has_reality_settings(self):
        """Test that server config has Reality TLS settings."""
        template = load_template("xray", "config.json.j2")
        test_vars = load_test_variables()

        result = template.render(**test_vars)
        config = json.loads(result)

        stream_settings = config["inbounds"][0]["streamSettings"]
        assert stream_settings["security"] == "reality"
        assert "realitySettings" in stream_settings

        reality = stream_settings["realitySettings"]
        assert reality["dest"] == test_vars["xray_reality_dest"]
        assert test_vars["xray_reality_sni"] in reality["serverNames"]

    def test_server_config_includes_all_users(self):
        """Test that all users are included in server config."""
        template = load_template("xray", "config.json.j2")
        test_vars = load_test_variables()

        result = template.render(**test_vars)
        config = json.loads(result)

        clients = config["inbounds"][0]["settings"]["clients"]
        client_ids = [c["id"] for c in clients]

        # All user UUIDs should be present
        for user, uuid in test_vars["xray_user_uuids"].items():
            if user in test_vars["users"]:
                assert uuid in client_ids, f"User {user} UUID not found in config"

    def test_server_config_has_correct_flow(self):
        """Test that XTLS flow is configured correctly."""
        template = load_template("xray", "config.json.j2")
        test_vars = load_test_variables()

        result = template.render(**test_vars)
        config = json.loads(result)

        clients = config["inbounds"][0]["settings"]["clients"]
        for client in clients:
            assert client["flow"] == test_vars["xray_flow"]

    def test_server_config_blocks_private_ips(self):
        """Test that routing blocks private IP ranges."""
        template = load_template("xray", "config.json.j2")
        test_vars = load_test_variables()

        result = template.render(**test_vars)
        config = json.loads(result)

        # Check routing rules
        assert "routing" in config
        rules = config["routing"]["rules"]

        # Should have a rule blocking private IPs
        private_ip_rule = None
        for rule in rules:
            if "geoip:private" in rule.get("ip", []):
                private_ip_rule = rule
                break

        assert private_ip_rule is not None, "No rule blocking private IPs"
        assert private_ip_rule["outboundTag"] == "block"


class TestXrayVlessLink:
    """Tests for VLESS share link generation."""

    def test_vless_link_format(self):
        """Test that VLESS link has correct format."""
        template = load_template("xray", "vless-link.txt.j2")
        test_vars = load_test_variables()
        test_vars["item"] = "alice"
        test_vars["user_uuid"] = test_vars["xray_user_uuids"]["alice"]

        result = template.render(**test_vars).strip()

        # Should start with vless://
        assert result.startswith("vless://"), f"Link should start with vless://, got: {result[:20]}"

        # Parse the URI
        parsed = urllib.parse.urlparse(result)
        assert parsed.scheme == "vless"

    def test_vless_link_contains_uuid(self):
        """Test that VLESS link contains user UUID."""
        template = load_template("xray", "vless-link.txt.j2")
        test_vars = load_test_variables()
        test_vars["item"] = "bob"
        test_vars["user_uuid"] = test_vars["xray_user_uuids"]["bob"]

        result = template.render(**test_vars).strip()

        assert test_vars["user_uuid"] in result

    def test_vless_link_contains_reality_params(self):
        """Test that VLESS link contains Reality parameters."""
        template = load_template("xray", "vless-link.txt.j2")
        test_vars = load_test_variables()
        test_vars["item"] = "alice"
        test_vars["user_uuid"] = test_vars["xray_user_uuids"]["alice"]

        result = template.render(**test_vars).strip()

        # Parse query parameters
        parsed = urllib.parse.urlparse(result)
        params = urllib.parse.parse_qs(parsed.query)

        assert params.get("security") == ["reality"]
        assert params.get("sni") == [test_vars["xray_reality_sni"]]
        assert params.get("flow") == [test_vars["xray_flow"]]
        assert "pbk" in params  # public key

    def test_vless_link_has_correct_server(self):
        """Test that VLESS link points to correct server."""
        template = load_template("xray", "vless-link.txt.j2")
        test_vars = load_test_variables()
        test_vars["item"] = "alice"
        test_vars["user_uuid"] = test_vars["xray_user_uuids"]["alice"]

        result = template.render(**test_vars).strip()

        # Should contain server IP and port
        assert f"@{test_vars['IP_subject_alt_name']}:{test_vars['xray_port']}" in result


class TestXrayClientConfig:
    """Tests for xray client configuration template."""

    def test_client_config_renders_valid_json(self):
        """Test that client config renders as valid JSON."""
        template = load_template("xray", "client-config.json.j2")
        test_vars = load_test_variables()
        test_vars["item"] = "alice"
        test_vars["user_uuid"] = test_vars["xray_user_uuids"]["alice"]

        result = template.render(**test_vars)

        # Should be valid JSON
        config = json.loads(result)
        assert isinstance(config, dict)

    def test_client_config_has_vless_outbound(self):
        """Test that client config has VLESS outbound."""
        template = load_template("xray", "client-config.json.j2")
        test_vars = load_test_variables()
        test_vars["item"] = "alice"
        test_vars["user_uuid"] = test_vars["xray_user_uuids"]["alice"]

        result = template.render(**test_vars)
        config = json.loads(result)

        # Find VLESS outbound
        vless_outbound = None
        for outbound in config["outbounds"]:
            if outbound["protocol"] == "vless":
                vless_outbound = outbound
                break

        assert vless_outbound is not None

    def test_client_config_has_local_proxies(self):
        """Test that client config has SOCKS and HTTP inbounds."""
        template = load_template("xray", "client-config.json.j2")
        test_vars = load_test_variables()
        test_vars["item"] = "alice"
        test_vars["user_uuid"] = test_vars["xray_user_uuids"]["alice"]

        result = template.render(**test_vars)
        config = json.loads(result)

        protocols = [inb["protocol"] for inb in config["inbounds"]]
        assert "socks" in protocols
        assert "http" in protocols


class TestXrayIptables:
    """Tests for xray firewall rules integration."""

    def test_iptables_accepts_xray_port(self):
        """Test that iptables rules accept traffic on xray port."""
        template_dir = Path(__file__).parent.parent.parent / "roles" / "common" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("rules.v4.j2")

        test_vars = load_test_variables()
        test_vars["xray_enabled"] = True

        result = template.render(**test_vars)

        # Should have rule accepting xray port
        assert f"--dport {test_vars['xray_port']}" in result
        assert "VLESS" in result or "xray" in result.lower()

    def test_iptables_no_xray_when_disabled(self):
        """Test that no xray rules when xray_enabled is false."""
        template_dir = Path(__file__).parent.parent.parent / "roles" / "common" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("rules.v4.j2")

        test_vars = load_test_variables()
        test_vars["xray_enabled"] = False

        result = template.render(**test_vars)

        # Should NOT have VLESS-specific rules
        assert "VLESS" not in result


class TestXrayConfigValidation:
    """Tests for xray configuration validation."""

    def test_reality_sni_matches_dest(self):
        """Test that Reality SNI and destination are consistent."""
        test_vars = load_test_variables()

        # SNI should be the hostname part of dest
        dest_host = test_vars["xray_reality_dest"].split(":")[0]
        assert test_vars["xray_reality_sni"] == dest_host

    def test_short_id_is_hex(self):
        """Test that short_id is valid hex string."""
        test_vars = load_test_variables()

        short_id = test_vars["xray_reality_short_id"]
        assert re.match(r"^[0-9a-f]+$", short_id, re.IGNORECASE)

    def test_user_uuids_are_valid(self):
        """Test that user UUIDs are valid UUID format."""
        test_vars = load_test_variables()
        uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

        for user, uuid in test_vars["xray_user_uuids"].items():
            assert uuid_pattern.match(uuid), f"Invalid UUID for {user}: {uuid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
