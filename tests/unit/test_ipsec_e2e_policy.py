"""Policy guardrails for the privileged IPsec tunnel integration test."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
E2E_SCRIPT = ROOT / "tests/e2e/test-vpn-connectivity.sh"
WORKFLOW = ROOT / ".github/workflows/integration-tests.yml"


def _script() -> str:
    return E2E_SCRIPT.read_text(encoding="utf-8")


def test_ipsec_e2e_runs_an_isolated_swanctl_client_and_requires_both_sas():
    script = _script()

    assert E2E_SCRIPT.stat().st_mode & 0o111, "E2E script must be directly executable"

    assert 'ip netns exec "${NAMESPACE}"' in script
    assert "charon" in script
    assert "swanctl --load-all" in script
    assert "swanctl --initiate" in script
    assert "swanctl --list-sas" in script
    assert 'grep -q "ESTABLISHED"' in script
    assert 'grep -q "INSTALLED"' in script
    assert "Full tunnel test requires" not in script


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
    assert "swanctl --terminate" in script
    assert 'kill "${IPSEC_CLIENT_PID}"' in script
    assert 'rm -rf "${IPSEC_CLIENT_DIR}"' in script
    assert "set -x" not in script


def test_integration_workflow_installs_and_exercises_swanctl_without_exporting_credentials():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["localhost-deployment"]
    serialized = yaml.safe_dump(job)

    assert "strongswan-swanctl" in serialized
    assert "libcharon-extra-plugins" in serialized
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
