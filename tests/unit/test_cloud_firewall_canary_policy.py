"""Policy tests for the credentialed cloud firewall canary workflow."""

import os
import subprocess
from pathlib import Path

import pytest
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


def test_canary_uses_run_attempt_specific_name_and_owner():
    environment = _workflow()["jobs"]["canary"]["env"]

    assert environment["CANARY_NAME"] == "algo-firewall-canary-${{ github.run_id }}-${{ github.run_attempt }}"
    assert environment["CANARY_OWNER"] == "algo-${{ github.run_id }}-${{ github.run_attempt }}"


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
    assert "./algo destroy" not in cleanup["run"]
    assert "aws cloudformation delete-stack" in cleanup["run"]
    assert "gcloud compute instances delete" in cleanup["run"]
    assert "GCE_INSTANCE_ID" in cleanup["run"]
    assert "GCE_FIREWALL_ID" in cleanup["run"]
    assert "GCE_NETWORK_ID" in cleanup["run"]
    assert "EC2_STACK_ID" in cleanup["run"]
    assert "--output json" in cleanup["run"]
    assert "jq -r '. // empty'" in cleanup["run"]
    assert 'if [[ -z "${EC2_STACK_ID:-}"' not in cleanup["run"]
    assert 'if [[ -z "${GCE_INSTANCE_ID:-}"' not in cleanup["run"]
    assert "GCE_FALLBACK_SAFE" not in cleanup["run"]
    assert "--all" not in cleanup["run"]
    preflight = next(step for step in steps if step.get("name") == "Preflight dedicated GCE project")
    assert '--filter="name=$CANARY_NAME"' in preflight["run"]
    assert "GCE_FALLBACK_SAFE" not in preflight["run"]


def test_gce_fallback_requires_discovered_immutable_ownership_ids():
    steps = _workflow()["jobs"]["canary"]["steps"]
    cleanup = next(step for step in steps if step.get("name") == "Destroy canary")

    assert '"$NEED_FALLBACK" == "true" && "$PROVIDER" == "gce"' in cleanup["run"]
    for proof in ("GCE_INSTANCE_ID", "GCE_INSTANCE_ZONE", "GCE_FIREWALL_ID", "GCE_NETWORK_ID"):
        assert proof in cleanup["run"]


@pytest.mark.parametrize("record_ids", [True, False])
def test_gce_fallback_discovers_and_deletes_only_exact_owned_resources(tmp_path, record_ids):
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
        "  printf '%s\\n' \"$CANARY_NAME,instance-123,us-central1-a,$CANARY_OWNER\"\n"
        "elif [[ \"$*\" == *'firewall-rules list'* ]]; then\n"
        "  printf '%s\\n' \"algovpn,firewall-123,algo-canary-owner=$CANARY_OWNER\"\n"
        "elif [[ \"$*\" == *'networks list'* ]]; then\n"
        "  printf '%s\\n' \"algovpn,network-123,algo-canary-owner=$CANARY_OWNER\"\n"
        "fi\n",
        encoding="utf-8",
    )
    gcloud.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "PROVIDER": "gce",
        "GCE_PROJECT": "dedicated-canary-project",
        "CANARY_NAME": "algo-firewall-canary-123",
        "CANARY_OWNER": "algo-123-1",
        "RUNNER_TEMP": str(tmp_path),
        "CALL_LOG": str(call_log),
    }
    if record_ids:
        environment.update(
            {
                "GCE_INSTANCE_ID": "instance-123",
                "GCE_INSTANCE_ZONE": "us-central1-a",
                "GCE_FIREWALL_ID": "firewall-123",
                "GCE_NETWORK_ID": "network-123",
            }
        )

    result = subprocess.run(["bash", "-c", cleanup], env=environment, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    calls = call_log.read_text(encoding="utf-8")
    assert "instances delete algo-firewall-canary-123" in calls
    assert "firewall-rules delete algovpn" in calls
    assert "networks delete algovpn" in calls
    assert "--project=dedicated-canary-project" in calls
    assert "--all" not in calls
    assert "unknown" not in calls


def test_ec2_fallback_discovers_owned_partial_stack_before_deleting(tmp_path):
    steps = _workflow()["jobs"]["canary"]["steps"]
    cleanup = next(step for step in steps if step.get("name") == "Destroy canary")["run"]
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    call_log = tmp_path / "calls"
    aws = fake_bin / "aws"
    aws.write_text(
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$*" >> "$CALL_LOG"\n'
        "if [[ \"$*\" == *'list-stacks'* ]]; then\n"
        "  printf '%s\\n' '\"arn:aws:cloudformation:us-east-1:123456789012:stack/algo-firewall-canary-123/stack-id\"'\n"
        "elif [[ \"$*\" == *'describe-stacks'* ]]; then\n"
        "  printf '%s\\t%s\\t%s\\n' "
        "'arn:aws:cloudformation:us-east-1:123456789012:stack/algo-firewall-canary-123/stack-id' "
        '"$CANARY_NAME" "$CANARY_OWNER"\n'
        "fi\n",
        encoding="utf-8",
    )
    aws.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "PROVIDER": "ec2",
        "CANARY_NAME": "algo-firewall-canary-123",
        "CANARY_OWNER": "algo-123-1",
        "CALL_LOG": str(call_log),
    }

    result = subprocess.run(["bash", "-c", cleanup], env=environment, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    calls = call_log.read_text(encoding="utf-8")
    assert "list-stacks" in calls
    assert "delete-stack --stack-name arn:aws:cloudformation:" in calls


def test_gce_cleanup_lookup_failure_refuses_all_deletes(tmp_path):
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

    assert result.returncode != 0


def test_gce_preflight_api_failure_never_records_cleanup_ownership(tmp_path):
    steps = _workflow()["jobs"]["canary"]["steps"]
    preflight = next(step for step in steps if step.get("name") == "Preflight dedicated GCE project")["run"]
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gcloud = fake_bin / "gcloud"
    gcloud.write_text(
        "#!/usr/bin/env bash\nif [[ \"$*\" == *'instances list'* ]]; then exit 0; fi\nexit 42\n",
        encoding="utf-8",
    )
    gcloud.chmod(0o700)
    github_env = tmp_path / "github-env"
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "GCE_PROJECT": "dedicated-canary-project",
        "CANARY_NAME": "algo-firewall-canary-123",
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_ENV": str(github_env),
    }

    result = subprocess.run(["bash", "-c", preflight], env=environment, capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert not github_env.exists() or "GCE_FALLBACK_SAFE" not in github_env.read_text(encoding="utf-8")


def test_exact_provider_cleanup_does_not_use_managed_destroy_by_name(tmp_path):
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
        "  printf '%s\\n' \"$CANARY_NAME,instance-123,us-central1-a,$CANARY_OWNER\"\n"
        "elif [[ \"$*\" == *'firewall-rules list'* ]]; then\n"
        "  printf '%s\\n' \"algovpn,firewall-123,algo-canary-owner=$CANARY_OWNER\"\n"
        "elif [[ \"$*\" == *'networks list'* ]]; then\n"
        "  printf '%s\\n' \"algovpn,network-123,algo-canary-owner=$CANARY_OWNER\"\n"
        "fi\n",
        encoding="utf-8",
    )
    gcloud.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "PROVIDER": "gce",
        "GCE_PROJECT": "dedicated-canary-project",
        "CANARY_NAME": "algo-firewall-canary-123",
        "CANARY_OWNER": "algo-123-1",
        "GCE_INSTANCE_ID": "instance-123",
        "GCE_INSTANCE_ZONE": "us-central1-a",
        "GCE_FIREWALL_ID": "firewall-123",
        "GCE_NETWORK_ID": "network-123",
        "CANARY_SERVER_IP": "192.0.2.10",
        "RUNNER_TEMP": str(tmp_path),
        "CALL_LOG": str(call_log),
    }

    result = subprocess.run(
        ["bash", "-c", cleanup], cwd=tmp_path, env=environment, capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "./algo destroy" not in cleanup
    calls = call_log.read_text(encoding="utf-8")
    assert "instances delete algo-firewall-canary-123" in calls


def test_gce_canary_uses_adc_application_auth_without_service_account_key():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    prompts = (ROOT / "roles/cloud-gce/tasks/prompts.yml").read_text(encoding="utf-8")
    provider_tasks = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "roles/cloud-gce/tasks/main.yml",
            ROOT / "roles/cloud-gce/tasks/destroy.yml",
            ROOT / "roles/cloud-gce/tasks/prompts.yml",
        )
    )

    assert "GCE_AUTH_KIND: application" in workflow
    assert "CANARY_GCE_SERVICE_ACCOUNT" in workflow
    assert "gce_auth_kind_effective" in prompts
    assert 'auth_kind: "{{ gce_auth_kind_effective }}"' in provider_tasks
    assert (
        "service_account_file: \"{{ omit if gce_auth_kind_effective == 'application' "
        'else credentials_file_path }}"' in provider_tasks
    )


def test_gce_oidc_is_refreshed_before_each_long_transition_and_cleanup():
    steps = _workflow()["jobs"]["canary"]["steps"]
    names = [step.get("name") for step in steps]
    refreshes = [
        index for index, step in enumerate(steps) if step.get("uses", "").startswith("google-github-actions/auth@")
    ]

    assert len(refreshes) >= 4
    for operation in (
        "Deploy both protocols",
        "Transition to WireGuard only",
        "Transition to IPsec only",
        "Destroy canary",
    ):
        operation_index = names.index(operation)
        assert any(refresh < operation_index for refresh in refreshes)
        if operation != "Deploy both protocols":
            prior_operation = max(
                names.index(candidate)
                for candidate in (
                    "Deploy both protocols",
                    "Transition to WireGuard only",
                    "Transition to IPsec only",
                )
                if candidate in names and names.index(candidate) < operation_index
            )
            assert any(prior_operation < refresh < operation_index for refresh in refreshes)

    cleanup_refresh = steps[max(index for index in refreshes if index < names.index("Destroy canary"))]
    assert cleanup_refresh["if"] == "${{ always() && inputs.provider == 'gce' }}"


def test_canary_records_and_verifies_run_specific_provider_ownership():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "CANARY_OWNER:" in workflow_text
    assert '-e "algo_canary_owner=$CANARY_OWNER"' in workflow_text
    assert "algo-canary-owner" in workflow_text
    assert "AlgoCanaryOwner" in workflow_text
    assert "GCE_FALLBACK_SAFE" not in workflow_text


def test_gce_cleanup_fails_closed_on_lookup_errors_and_ownership_mismatch():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    cleanup = workflow_text.split("- name: Destroy canary", 1)[1]

    assert "mapfile -t INSTANCE_ROWS < <(" not in cleanup
    assert "gcloud compute instances list" in cleanup
    assert "gcloud compute firewall-rules list" in cleanup
    assert "gcloud compute networks list" in cleanup
    assert "Ambiguous GCE instance ownership" in cleanup
    assert "Refusing fallback cleanup" in cleanup


def test_gce_cleanup_validates_every_owned_resource_before_first_delete():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    cleanup = workflow_text.split("- name: Destroy canary", 1)[1]

    first_delete = min(
        cleanup.index("gcloud compute instances delete"),
        cleanup.index("gcloud compute firewall-rules delete"),
        cleanup.index("gcloud compute networks delete"),
    )
    assert cleanup.index("Refusing fallback cleanup of an unowned GCE instance") < first_delete
    assert cleanup.index("Refusing fallback cleanup of an unowned GCE firewall") < first_delete
    assert cleanup.index("Refusing fallback cleanup of an unowned GCE network") < first_delete


def test_canary_never_enables_shell_tracing_or_prints_credentials():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "set -x" not in text
    assert "printenv" not in text
    assert "credentials_json" not in text
    assert "access-key" not in text.lower()
