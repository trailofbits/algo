"""Regression tests for deterministic VPN service orchestration."""

from pathlib import Path

ROOT = Path(__file__).parents[2]
SERVER_PLAYBOOK = ROOT / "server.yml"
E2E_CONNECTIVITY = ROOT / "tests/e2e/test-vpn-connectivity.sh"


def test_import_roles_are_not_run_as_unsupported_async_jobs():
    text = SERVER_PLAYBOOK.read_text(encoding="utf-8")

    assert "async_status:" not in text
    assert "poll: 0" not in text
    assert "performance_parallel_services | default(true)" not in text
    assert "Build async job list" not in text


def test_wireguard_deployment_verifies_loaded_peer_count():
    text = SERVER_PLAYBOOK.read_text(encoding="utf-8")

    assert "Verify WireGuard peer count" in text
    assert "wg show wg0 peers" in text
    assert "wireguard_peer_count.stdout_lines | length != users | length" in text


def test_ipsec_deployment_verifies_service_is_active():
    text = SERVER_PLAYBOOK.read_text(encoding="utf-8")

    assert "Collect service state for StrongSwan verification" in text
    assert "service_facts:" in text
    assert "Verify StrongSwan service is active" in text
    assert "ansible_facts.services[strongswan_service + '.service'].state == 'running'" in text


def test_dns_deployment_verifies_local_listener():
    text = SERVER_PLAYBOOK.read_text(encoding="utf-8")

    assert "Verify local DNS listener" in text
    assert 'host: "{{ local_service_ip }}"' in text
    assert "port: 53" in text


def test_e2e_does_not_restart_wireguard_to_repair_deployment():
    text = E2E_CONNECTIVITY.read_text(encoding="utf-8")

    assert "deployment handler bug" not in text
    assert "systemctl restart wg-quick@wg0" not in text
