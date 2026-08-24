#!/usr/bin/env python3
"""Query a canary provider firewall and verify the protocol transition matrix.

Only normalized protocol labels are emitted. Provider payloads, resource names,
account/project identifiers, addresses, and credentials are never printed or
persisted by this verifier.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple, Protocol
from urllib.parse import quote

TRANSITION_ORDER = ("both", "wireguard-only", "ipsec-only")
PUBLIC_RANGES = {"0.0.0.0/0", "::/0"}
PROJECT_PATTERN = re.compile(r"[a-z][a-z0-9-]{4,61}[a-z0-9]")
GCE_FIREWALL_PATTERN = re.compile(r"[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?")


class VerificationError(RuntimeError):
    """A sanitized verification failure suitable for CI output."""


class ProviderQueryError(RuntimeError):
    """A provider API failure whose original details must not be printed."""


class IngressRule(NamedTuple):
    protocol: str
    from_port: int | None
    to_port: int | None
    source: str


class FirewallAdapter(Protocol):
    def query(self, resource_id: str) -> set[IngressRule]: ...


def _source_kinds(values: list[str], has_restricted_reference: bool = False) -> set[str]:
    kinds = {value if value in PUBLIC_RANGES else "restricted" for value in values}
    if has_restricted_reference or not values:
        kinds.add("restricted")
    return kinds


class EC2Adapter:
    """Adapter for the EC2 DescribeSecurityGroups API."""

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            import boto3

            client = boto3.client("ec2")
        self._client = client

    def query(self, resource_id: str) -> set[IngressRule]:
        try:
            response = self._client.describe_security_groups(GroupIds=[resource_id])
            groups = response.get("SecurityGroups", [])
            if len(groups) != 1:
                raise ProviderQueryError("provider API returned an unexpected firewall count")
            rules: set[IngressRule] = set()
            for permission in groups[0].get("IpPermissions", []):
                protocol = str(permission.get("IpProtocol", ""))
                from_port = permission.get("FromPort")
                to_port = permission.get("ToPort")
                ranges = [item["CidrIp"] for item in permission.get("IpRanges", []) if "CidrIp" in item]
                ranges += [item["CidrIpv6"] for item in permission.get("Ipv6Ranges", []) if "CidrIpv6" in item]
                restricted_reference = bool(permission.get("UserIdGroupPairs") or permission.get("PrefixListIds"))
                for source in _source_kinds(ranges, restricted_reference):
                    rules.add(IngressRule(protocol, from_port, to_port, source))
            return rules
        except ProviderQueryError:
            raise
        except Exception:
            raise ProviderQueryError("provider API query failed") from None


class GCEAdapter:
    """Adapter for the GCE firewalls.list REST API."""

    def __init__(self, project: str, session: Any | None = None) -> None:
        if not PROJECT_PATTERN.fullmatch(project):
            raise VerificationError("GCE project configuration is invalid")
        if session is None:
            import google.auth
            from google.auth.transport.requests import AuthorizedSession

            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/compute.readonly"])
            session = AuthorizedSession(credentials)
        self._project = project
        self._session = session

    def query(self, resource_id: str) -> set[IngressRule]:
        if not GCE_FIREWALL_PATTERN.fullmatch(resource_id):
            raise VerificationError("GCE firewall resource identifier is invalid")
        try:
            project = quote(self._project, safe="")
            url = f"https://compute.googleapis.com/compute/v1/projects/{project}/global/firewalls"
            response = self._session.get(url, params={"filter": f'name="{resource_id}"'}, timeout=30)
            response.raise_for_status()
            items = response.json().get("items", [])
            if len(items) != 1 or items[0].get("direction", "INGRESS") != "INGRESS" or items[0].get("disabled", False):
                raise ProviderQueryError("provider API returned an unexpected firewall count")
            firewall = items[0]
            source_values = list(firewall.get("sourceRanges", []))
            restricted_reference = bool(firewall.get("sourceTags") or firewall.get("sourceServiceAccounts"))
            sources = _source_kinds(source_values, restricted_reference)
            rules: set[IngressRule] = set()
            for action, entries in (("", firewall.get("allowed", [])), ("deny:", firewall.get("denied", []))):
                for entry in entries:
                    protocol = action + str(entry.get("IPProtocol", ""))
                    ports = entry.get("ports") or [None]
                    for port in ports:
                        from_port, to_port = _parse_gce_port(port)
                        for source in sources:
                            rules.add(IngressRule(protocol, from_port, to_port, source))
            return rules
        except ProviderQueryError:
            raise
        except Exception:
            raise ProviderQueryError("provider API query failed") from None


def _parse_gce_port(port: str | None) -> tuple[int | None, int | None]:
    if port is None:
        return None, None
    start, separator, end = str(port).partition("-")
    return int(start), int(end if separator else start)


def expected_rules(provider: str, stage: str, ssh_port: int, wireguard_port: int) -> set[IngressRule]:
    if provider not in {"ec2", "gce"} or stage not in TRANSITION_ORDER:
        raise VerificationError("unsupported provider or transition stage")
    public_ipv4 = "0.0.0.0/0"
    rules = {IngressRule("tcp", ssh_port, ssh_port, public_ipv4)}
    if provider == "gce":
        rules.add(IngressRule("icmp", None, None, public_ipv4))
    if stage in {"both", "ipsec-only"}:
        rules.update(
            {
                IngressRule("udp", 500, 500, public_ipv4),
                IngressRule("udp", 4500, 4500, public_ipv4),
            }
        )
    if stage in {"both", "wireguard-only"}:
        rules.add(IngressRule("udp", wireguard_port, wireguard_port, public_ipv4))
    return rules


def assert_stage(
    provider: str,
    stage: str,
    observed: set[IngressRule],
    ssh_port: int,
    wireguard_port: int,
) -> None:
    if observed != expected_rules(provider, stage, ssh_port, wireguard_port):
        raise VerificationError("firewall does not match the exact expected ingress policy")


def load_history(state_file: Path) -> dict[str, Any]:
    if not state_file.exists():
        return {"provider": None, "stages": []}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise VerificationError("transition state is invalid") from None
    if set(data) != {"provider", "stages"} or not isinstance(data["stages"], list):
        raise VerificationError("transition state is invalid")
    return data


def record_transition(state_file: Path, provider: str, stage: str) -> None:
    history = load_history(state_file)
    stages = history["stages"]
    if history["provider"] not in {None, provider}:
        raise VerificationError("transition order or provider changed unexpectedly")
    expected_next = TRANSITION_ORDER[len(stages)] if len(stages) < len(TRANSITION_ORDER) else None
    if stage != expected_next:
        raise VerificationError("transition order is invalid")
    sanitized = {"provider": provider, "stages": [*stages, stage]}
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(sanitized, separators=(",", ":")), encoding="utf-8")
    state_file.chmod(0o600)


def _rule_label(rule: IngressRule, ssh_port: int = 4160, wireguard_port: int = 51820) -> str:
    public_ipv4 = "0.0.0.0/0"
    keys = {
        IngressRule("tcp", ssh_port, ssh_port, public_ipv4): "ssh",
        IngressRule("udp", 500, 500, public_ipv4): "ipsec-500",
        IngressRule("udp", 4500, 4500, public_ipv4): "ipsec-4500",
        IngressRule("udp", wireguard_port, wireguard_port, public_ipv4): "wireguard",
        IngressRule("icmp", None, None, public_ipv4): "icmp",
    }
    return keys.get(rule, "unexpected")


def sanitized_summary(
    provider: str,
    stage: str,
    rules: set[IngressRule],
    ssh_port: int = 4160,
    wireguard_port: int = 51820,
) -> str:
    labels = sorted({_rule_label(rule, ssh_port, wireguard_port) for rule in rules})
    return f"verified provider={provider} stage={stage} ingress={','.join(labels)}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a provider firewall without emitting provider payloads")
    parser.add_argument("--provider", required=True, choices=("ec2", "gce"))
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--stage", required=True, choices=TRANSITION_ORDER)
    parser.add_argument("--state-file", required=True, type=Path)
    parser.add_argument("--ssh-port", type=int, default=4160)
    parser.add_argument("--wireguard-port", type=int, default=51820)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.provider == "ec2":
            adapter: FirewallAdapter = EC2Adapter()
        else:
            adapter = GCEAdapter(project=os.environ.get("GCE_PROJECT", ""))
        observed = adapter.query(args.resource_id)
        assert_stage(args.provider, args.stage, observed, args.ssh_port, args.wireguard_port)
        record_transition(args.state_file, args.provider, args.stage)
        print(sanitized_summary(args.provider, args.stage, observed, args.ssh_port, args.wireguard_port))
        return 0
    except VerificationError as error:
        print(f"verification failed: {error}", file=sys.stderr)
    except ProviderQueryError:
        print("verification failed: provider API query failed", file=sys.stderr)
    except Exception:
        print("verification failed: internal verifier error", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
