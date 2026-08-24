"""Policy tests for the credentialed cloud firewall canary workflow."""

import os
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
WORKFLOW_PATH = ROOT / ".github/workflows/provider-firewall-canary.yml"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_canary_is_manual_only_and_provider_limited():
    workflow = _workflow()

    assert set(workflow["on"]) == {"workflow_dispatch"}
    provider = workflow["on"]["workflow_dispatch"]["inputs"]["provider"]
    assert provider["type"] == "choice"
    assert provider["options"] == ["ec2", "gce"]
    assert "azure" not in provider["options"]
    assert "lightsail" not in provider["options"]


def test_canary_uses_oidc_least_privilege_and_provider_lock():
    workflow = _workflow()

    assert workflow["permissions"] == {"contents": "read", "id-token": "write"}
    assert workflow["concurrency"]["group"] == "provider-firewall-canary-${{ inputs.provider }}"
    assert workflow["concurrency"]["cancel-in-progress"] is False


def test_canary_verifies_every_transition_and_always_destroys():
    workflow = _workflow()
    steps = workflow["jobs"]["canary"]["steps"]
    names = [step.get("name") for step in steps]

    assert names.index("Verify both protocols") < names.index("Verify WireGuard only")
    assert names.index("Verify WireGuard only") < names.index("Verify IPsec only")
    assert any("./algo list-servers" in step.get("run", "") for step in steps)
    cleanup = next(step for step in steps if step.get("name") == "Destroy canary")
    assert cleanup["if"] == "${{ always() }}"
    assert "./algo destroy" in cleanup["run"]
    assert "aws cloudformation delete-stack" in cleanup["run"]
    assert "gcloud compute instances delete" in cleanup["run"]
    assert '"$CANARY_NAME"' in cleanup["run"]
    assert "GCE_FALLBACK_SAFE" in cleanup["run"]
    assert "--all" not in cleanup["run"]
    preflight = next(step for step in steps if step.get("name") == "Preflight dedicated GCE project")
    assert '--filter="name=$CANARY_NAME"' in preflight["run"]
    assert "GCE_FALLBACK_SAFE=true" in preflight["run"]


def test_gce_cleanup_does_not_depend_on_managed_server_discovery():
    steps = _workflow()["jobs"]["canary"]["steps"]
    cleanup = next(step for step in steps if step.get("name") == "Destroy canary")

    assert 'elif [[ "$PROVIDER" == "gce" && "${GCE_FALLBACK_SAFE:-}" == "true" ]]' in cleanup["run"]
    assert cleanup["run"].index('elif [[ "$PROVIDER" == "gce"') > cleanup["run"].index("CANARY_SERVER_IP")


def test_gce_fallback_after_pre_discovery_failure_deletes_only_exact_owned_names(tmp_path):
    steps = _workflow()["jobs"]["canary"]["steps"]
    cleanup = next(step for step in steps if step.get("name") == "Destroy canary")["run"]
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    call_log = tmp_path / "calls"
    gcloud = fake_bin / "gcloud"
    gcloud.write_text(
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$*" >> "$CALL_LOG"\n'
        "if [[ \"$*\" == *'instances list'* ]]; then\n"
        "  printf '%s\\n' \"$CANARY_NAME,us-central1-a\"\n"
        "fi\n",
        encoding="utf-8",
    )
    gcloud.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "PROVIDER": "gce",
        "GCE_FALLBACK_SAFE": "true",
        "GCE_PROJECT": "dedicated-canary-project",
        "CANARY_NAME": "algo-firewall-canary-123",
        "RUNNER_TEMP": str(tmp_path),
        "CALL_LOG": str(call_log),
    }

    result = subprocess.run(["bash", "-c", cleanup], env=environment, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    calls = call_log.read_text(encoding="utf-8")
    assert "instances delete algo-firewall-canary-123" in calls
    assert "firewall-rules delete algovpn" in calls
    assert "networks delete algovpn" in calls
    assert "--project=dedicated-canary-project" in calls
    assert "--all" not in calls
    assert "unknown" not in calls


def test_gce_cleanup_without_preflight_ownership_refuses_all_deletes(tmp_path):
    steps = _workflow()["jobs"]["canary"]["steps"]
    cleanup = next(step for step in steps if step.get("name") == "Destroy canary")["run"]
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gcloud = fake_bin / "gcloud"
    gcloud.write_text("#!/usr/bin/env bash\nexit 99\n", encoding="utf-8")
    gcloud.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "PROVIDER": "gce",
        "GCE_PROJECT": "project-with-preexisting-resources",
        "CANARY_NAME": "algo-firewall-canary-123",
        "RUNNER_TEMP": str(tmp_path),
    }

    result = subprocess.run(["bash", "-c", cleanup], env=environment, capture_output=True, text=True, check=False)

    assert result.returncode == 1
    assert "No canary ownership proof" in result.stdout


def test_canary_never_enables_shell_tracing_or_prints_credentials():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "set -x" not in text
    assert "printenv" not in text
    assert "credentials_json" not in text
    assert "access-key" not in text.lower()
