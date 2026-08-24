"""Unit tests for the live cloud firewall verifier."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "tests/e2e/verify-cloud-firewall.py"


def _load_verifier():
    spec = importlib.util.spec_from_file_location("cloud_firewall_verifier", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_ec2_adapter_normalizes_describe_security_groups_response():
    verifier = _load_verifier()

    class EC2Client:
        def describe_security_groups(self, **kwargs):
            assert kwargs == {"GroupIds": ["sg-private-id"]}
            return {
                "SecurityGroups": [
                    {
                        "IpPermissions": [
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 4160,
                                "ToPort": 4160,
                                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                            },
                            {
                                "IpProtocol": "udp",
                                "FromPort": 500,
                                "ToPort": 500,
                                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                            },
                            {
                                "IpProtocol": "udp",
                                "FromPort": 4500,
                                "ToPort": 4500,
                                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                            },
                            {
                                "IpProtocol": "udp",
                                "FromPort": 51820,
                                "ToPort": 51820,
                                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                            },
                        ]
                    }
                ]
            }

    observed = verifier.EC2Adapter(client=EC2Client()).query("sg-private-id")

    assert observed == verifier.expected_rules("ec2", "both", ssh_port=4160, wireguard_port=51820)


def test_gce_adapter_normalizes_firewalls_list_response():
    verifier = _load_verifier()

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "items": [
                    {
                        "name": "private-firewall-name",
                        "direction": "INGRESS",
                        "sourceRanges": ["0.0.0.0/0"],
                        "allowed": [
                            {"IPProtocol": "tcp", "ports": ["4160"]},
                            {"IPProtocol": "udp", "ports": ["500", "4500", "51820"]},
                            {"IPProtocol": "icmp"},
                        ],
                    }
                ]
            }

    class Session:
        def get(self, url, **kwargs):
            assert "/projects/private-project/global/firewalls" in url
            assert kwargs == {"params": {"filter": 'name="private-firewall-name"'}, "timeout": 30}
            return Response()

    adapter = verifier.GCEAdapter(project="private-project", session=Session())
    observed = adapter.query("private-firewall-name")

    assert observed == verifier.expected_rules("gce", "both", ssh_port=4160, wireguard_port=51820)


def test_gce_adapter_rejects_filter_injection_before_api_call():
    verifier = _load_verifier()

    class Session:
        def get(self, *_args, **_kwargs):
            pytest.fail("unsafe resource ID reached the provider API")

    adapter = verifier.GCEAdapter(project="private-project", session=Session())

    with pytest.raises(verifier.VerificationError, match="resource identifier"):
        adapter.query('name" OR name="other')


def test_exact_stage_assertion_rejects_extra_or_missing_ingress():
    verifier = _load_verifier()
    expected = verifier.expected_rules("ec2", "wireguard-only", 4160, 51820)
    extra = verifier.IngressRule("udp", 500, 500, "public")

    with pytest.raises(verifier.VerificationError, match="firewall does not match"):
        verifier.assert_stage("ec2", "wireguard-only", expected | {extra}, 4160, 51820)
    with pytest.raises(verifier.VerificationError, match="firewall does not match"):
        verifier.assert_stage("ec2", "wireguard-only", expected - {next(iter(expected))}, 4160, 51820)


def test_transition_history_requires_both_then_wireguard_then_ipsec(tmp_path):
    verifier = _load_verifier()
    state_file = tmp_path / "states.json"

    verifier.record_transition(state_file, "ec2", "both")
    verifier.record_transition(state_file, "ec2", "wireguard-only")
    verifier.record_transition(state_file, "ec2", "ipsec-only")

    assert verifier.load_history(state_file) == {"provider": "ec2", "stages": ["both", "wireguard-only", "ipsec-only"]}


@pytest.mark.parametrize("stages", [("wireguard-only",), ("both", "ipsec-only"), ("both", "both")])
def test_transition_history_rejects_skipped_or_repeated_stage(tmp_path, stages):
    verifier = _load_verifier()
    state_file = tmp_path / "states.json"

    with pytest.raises(verifier.VerificationError, match="transition order"):
        for stage in stages:
            verifier.record_transition(state_file, "ec2", stage)


def test_summary_is_sanitized_and_contains_only_rule_labels():
    verifier = _load_verifier()
    rules = verifier.expected_rules("ec2", "both", 4160, 51820)

    summary = verifier.sanitized_summary("ec2", "both", rules)

    public_range = ".".join(("0", "0", "0", "0")) + "/0"
    assert summary == "verified provider=ec2 stage=both ingress=ipsec-4500,ipsec-500,ssh,wireguard"
    assert "sg-" not in summary
    assert public_range not in summary
    assert "credential" not in summary.lower()
