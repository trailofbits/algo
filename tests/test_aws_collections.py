"""Exercise AWS collection requests with botocore's validated HTTP stubs."""

import importlib
import io
import json
import os
import secrets
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path

import pytest
from ansible.module_utils import basic


@pytest.fixture
def aws(monkeypatch, tmp_path):
    if os.environ.get("ALGO_CLOUD_SMOKE") == "1":
        boto3 = importlib.import_module("boto3")
    else:
        boto3 = pytest.importorskip("boto3", reason="Install the aws extra")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "credentials"))
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    def client(service):
        connection = boto3.client(
            service,
            region_name="us-east-1",
            aws_access_key_id="fixture-access",
            aws_secret_access_key=secrets.token_hex(16),
        )
        monkeypatch.setattr(boto3.session.Session, "client", lambda *_args, **_kwargs: connection)
        return connection

    return client


def run_module(monkeypatch, name, arguments):
    module = importlib.import_module(f"ansible_collections.amazon.aws.plugins.modules.{name}")
    manifest = Path(module.__file__).parents[2] / "MANIFEST.json"
    assert json.loads(manifest.read_text())["collection_info"]["version"] == "12.1.0"
    parameters = {
        "region": "us-east-1",
        "aws_access_key": "fixture-access",
        "aws_secret_key": "fixture-secret",
        **arguments,
    }
    module_args = json.dumps({"ANSIBLE_MODULE_ARGS": parameters}).encode()
    monkeypatch.setattr(basic, "_ANSIBLE_ARGS", module_args)
    monkeypatch.setattr(basic, "_ANSIBLE_PROFILE", "legacy")
    output = io.StringIO()
    with redirect_stdout(output), pytest.raises(SystemExit) as status:
        module.main()
    result = json.loads(output.getvalue())
    assert status.value.code == 0, result
    return result


def test_ec2_image_discovery_uses_boto3_and_returns_expected_fields(aws, monkeypatch):
    from botocore.stub import Stubber

    client = aws("ec2")
    with Stubber(client) as stub:
        stub.add_response(
            "describe_images",
            {
                "Images": [
                    {"ImageId": "ami-fixture", "CreationDate": "2026-11-01T00:00:00Z"},
                ]
            },
            {
                "Filters": [
                    {"Name": "architecture", "Values": ["x86_64"]},
                    {"Name": "owner-id", "Values": ["099720109477"]},
                ]
            },
        )
        result = run_module(
            monkeypatch,
            "ec2_ami_info",
            {
                "owners": "099720109477",
                "filters": {"architecture": "x86_64"},
            },
        )
        stub.assert_no_pending_responses()
    assert result["images"][0]["image_id"] == "ami-fixture"
    assert result["images"][0]["creation_date"] == "2026-11-01T00:00:00Z"


def test_cloudformation_creates_template_body_and_returns_stack_outputs(aws, monkeypatch):
    from botocore.stub import ANY, Stubber

    client = aws("cloudformation")
    body = '{"Resources": {}}'
    stack = {
        "StackName": "algo-test",
        "StackId": "stack-id",
        "StackStatus": "CREATE_COMPLETE",
        "CreationTime": datetime(2026, 11, 1, tzinfo=UTC),
        "Outputs": [{"OutputKey": "ElasticIP", "OutputValue": "192.0.2.1"}],
    }
    with Stubber(client) as stub:
        stub.add_client_error(
            "describe_stacks",
            service_error_code="ValidationError",
            service_message="Stack does not exist",
            expected_params={"StackName": "algo-test"},
        )
        stub.add_response(
            "create_stack",
            {"StackId": "stack-id"},
            {
                "StackName": "algo-test",
                "TemplateBody": body,
                "Parameters": [],
                "Capabilities": ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                "ClientRequestToken": ANY,
                "NotificationARNs": [],
                "DisableRollback": False,
            },
        )
        stub.add_response("describe_stacks", {"Stacks": [stack]}, {"StackName": "stack-id"})
        stub.add_response("describe_stack_events", {"StackEvents": []}, {"StackName": "stack-id"})
        stub.add_response("describe_stacks", {"Stacks": [stack]}, {"StackName": "algo-test"})
        stub.add_response(
            "list_stack_resources",
            {"StackResourceSummaries": []},
            {"StackName": "algo-test"},
        )
        result = run_module(
            monkeypatch,
            "cloudformation",
            {"stack_name": "algo-test", "template_body": body},
        )
        stub.assert_no_pending_responses()
    assert result["changed"]
    assert result["stack_outputs"]["ElasticIP"] == "192.0.2.1"
