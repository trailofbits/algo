"""Policy guardrails for the privileged IPsec tunnel integration test."""

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
E2E_SCRIPT = ROOT / "tests/e2e/test-vpn-connectivity.sh"
WORKFLOW = ROOT / ".github/workflows/integration-tests.yml"
XFRM_COUNTER = ROOT / "tests/e2e/xfrm-byte-count.awk"


def _script() -> str:
    return E2E_SCRIPT.read_text(encoding="utf-8")


def test_ipsec_e2e_runs_an_isolated_swanctl_client_and_requires_both_sas():
    script = _script()

    assert E2E_SCRIPT.stat().st_mode & 0o111, "E2E script must be directly executable"

    assert 'ip netns exec "${NAMESPACE}"' in script
    assert "unshare --mount --pid --fork --kill-child --mount-proc" in script
    assert "mount -t tmpfs" in script and "tmpfs /run" in script
    assert "charon" in script
    assert '"${IPSEC_SWANCTL_BINARY}" --load-all' in script
    assert '"${IPSEC_SWANCTL_BINARY}" --initiate' in script
    assert '"${IPSEC_SWANCTL_BINARY}" --list-sas' in script
    assert 'grep -q "ESTABLISHED"' in script
    assert 'grep -q "INSTALLED"' in script
    assert "Full tunnel test requires" not in script


def test_ipsec_client_uses_a_private_executable_path_outside_host_apparmor_attachment():
    script = _script()

    assert 'install -m 0700 "${charon_binary}" "${IPSEC_CLIENT_DIR}/charon-client"' in script
    assert 'charon_binary="${IPSEC_CLIENT_DIR}/charon-client"' in script
    assert "command -v charon" not in script
    assert 'stat -c "%u" -- "${candidate}"' in script
    assert 'stat -c "%a" -- "${candidate}"' in script
    assert '|| -L "${candidate}"' in script


def test_ipsec_client_uses_a_private_swanctl_path_outside_host_apparmor_attachment():
    script = _script()

    assert 'install -m 0700 "${swanctl_binary}" "${IPSEC_CLIENT_DIR}/swanctl-client"' in script
    assert 'IPSEC_SWANCTL_BINARY="${IPSEC_CLIENT_DIR}/swanctl-client"' in script
    assert 'ip netns exec "${NAMESPACE}" swanctl --' not in script


def test_ipsec_client_strongswan_config_uses_parser_safe_dynamic_values():
    script = _script()

    assert "${charon_log} {" not in script
    assert "stderr {" in script
    assert 'socket = "unix://${vici_socket}"' in script


def test_ipsec_e2e_proves_dns_and_routed_source_ip_through_the_tunnel():
    script = _script()

    assert 'ip netns exec "${NAMESPACE}" dig' in script
    assert 'ip netns exec "${NAMESPACE}" curl' in script
    assert "VPN source IP does not match server source IP" in script
    assert "remote_ts = 0.0.0.0/0" in script


def test_ipsec_client_credentials_are_private_and_torn_down():
    script = _script()

    assert "umask 077" in script
    assert 'chmod 700 "${IPSEC_CLIENT_DIR}"' in script
    assert '"${IPSEC_SWANCTL_BINARY}" --terminate' in script
    assert 'kill "${IPSEC_CLIENT_PID}"' in script
    assert 'rm -rf "${IPSEC_CLIENT_DIR}"' in script
    assert "set -x" not in script


def test_ipsec_e2e_preserves_signal_failure_status():
    script = _script()

    assert "trap cleanup EXIT INT TERM" not in script
    assert "trap cleanup EXIT" in script
    assert "trap 'exit 130' INT" in script
    assert "trap 'exit 143' TERM" in script
    assert "trap - EXIT INT TERM" in script
    assert 'exit "${exit_code}"' in script


def test_ipsec_e2e_proves_traffic_with_xfrm_packet_counters():
    script = _script()

    assert "xfrm_bytes_before" in script
    assert "xfrm_bytes_after" in script
    assert "((xfrm_bytes_after > xfrm_bytes_before))" in script


def test_xfrm_counter_parses_single_and_two_line_iproute2_formats():
    fixture = """\
lifetime current: 20124(bytes), 83(packets)
lifetime current:
  100(bytes), 2(packets)
"""
    result = subprocess.run(
        ["awk", "-f", str(XFRM_COUNTER)],
        input=fixture,
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == "20224"


def test_security_sensitive_tests_are_not_called_in_errexit_disabling_or_lists():
    script = _script()

    assert "test_ipsec ||" not in script
    assert "test_wireguard ||" not in script
    assert 'rm -rf "${IPSEC_CLIENT_DIR}" || return 1' in script


def test_privileged_network_sysctls_are_restored_on_exit():
    script = _script()

    assert "ORIGINAL_IP_FORWARD" in script
    assert "ORIGINAL_RP_FILTER_ALL" in script
    assert 'sysctl -w net.ipv4.ip_forward="${ORIGINAL_IP_FORWARD}"' in script
    assert 'sysctl -w net.ipv4.conf.all.rp_filter="${ORIGINAL_RP_FILTER_ALL}"' in script


def test_cleanup_tracks_and_removes_only_rules_the_harness_added():
    script = _script()

    for marker in ("NAT_RULE_ADDED", "WG_RULE_ADDED", "IKE_RULE_ADDED", "NATT_RULE_ADDED"):
        assert marker in script
    assert "iptables -t nat -D POSTROUTING" in script
    assert "iptables -D INPUT" in script
    cleanup = script.split("cleanup() {", 1)[1].split("trap cleanup EXIT", 1)[0]
    assert not any("iptables" in line and "|| true" in line for line in cleanup.splitlines())


def test_server_ipsec_cli_is_optional_for_swanctl_backend():
    script = _script()
    prerequisite_loop = next(line for line in script.splitlines() if line.strip().startswith("for cmd in "))

    assert " ipsec " not in f" {prerequisite_loop} "
    assert "ipsec statusall || true" in script


def test_integration_workflow_installs_and_exercises_swanctl_without_exporting_credentials():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["localhost-deployment"]
    serialized = yaml.safe_dump(job)

    assert "strongswan-swanctl" in serialized
    assert "libcharon-extra-plugins" in serialized
    assert "libxml2-utils" in serialized
    assert "tests/e2e/test-vpn-connectivity.sh" in serialized
    assert "algo_no_log: true" in serialized
    assert "test-ca-password" not in serialized
    assert "test-p12-password" not in serialized
    assert "openssl rand -hex" in serialized
    assert "rm -f integration-test.cfg" in serialized
    deployment_step = next(step for step in job["steps"] if step.get("name") == "Run Algo deployment")
    assert "-vv" not in deployment_step["run"]
    assert "cat configs/" not in serialized
    artifact_paths = [
        step.get("with", {}).get("path", "")
        for step in job["steps"]
        if "actions/upload-artifact@" in step.get("uses", "")
    ]
    assert all("configs/" not in path for path in artifact_paths)
    pull_request_paths = workflow["on"]["pull_request"]["paths"]
    assert ".github/workflows/integration-tests.yml" in pull_request_paths
    assert "tests/e2e/**" in pull_request_paths
