"""Exercise the real Ansible module with only HTTP and waiting replaced."""

import json
from io import BytesIO
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
import scaleway_instance
from ansible.module_utils import basic

SERVER = {
    "id": "server-id",
    "name": "algo",
    "state": "stopped",
    "tags": [],
    "dynamic_ip_required": True,
}
CREATE = {"image": "image-id", "organization": "org-id", "commercial_type": "DEV1-S"}


@pytest.fixture
def run_instance(monkeypatch, capsys):
    clock = SimpleNamespace(monotonic=lambda: 0, sleep=lambda _seconds: None)
    monkeypatch.setattr(scaleway_instance, "time", clock)

    def run(arguments, responses):
        requests = []
        pending = iter(responses)

        def fetch_url(_module, url, **kwargs):
            parsed = urlsplit(url)
            assert parsed.netloc == "api.scaleway.com"
            assert parsed.path.startswith("/instance/v1/zones/nl-ams-2/")
            assert kwargs["headers"]["X-Auth-Token"] == "fixture-token"
            body = json.loads(kwargs["data"]) if kwargs["data"] is not None else None
            requests.append((kwargs["method"], parsed.path, parse_qs(parsed.query), body))
            status, data = next(pending)
            raw = data if isinstance(data, bytes) else json.dumps(data).encode()
            return BytesIO(raw), {"status": status}

        monkeypatch.setattr(scaleway_instance, "fetch_url", fetch_url)
        parameters = {"name": "algo", "zone": "nl-ams-2", "api_token": "fixture-token", **arguments}
        module_args = json.dumps({"ANSIBLE_MODULE_ARGS": parameters}).encode()
        monkeypatch.setattr(basic, "_ANSIBLE_ARGS", module_args)
        monkeypatch.setattr(basic, "_ANSIBLE_PROFILE", "legacy")
        with pytest.raises(SystemExit) as exit_status:
            scaleway_instance.main()
        result = json.loads(capsys.readouterr().out)
        assert exit_status.value.code == (1 if result.get("failed") else 0)
        assert "fixture-token" not in json.dumps(result)
        assert next(pending, None) is None, "The module skipped an expected HTTP operation"
        return result, requests

    return run


def test_create_selected_image(run_instance):
    result, requests = run_instance(
        {**CREATE, "tags": ["Environment:Algo"]},
        [(200, {"servers": []}), (200, {"image": {"id": "image-id"}}), (201, {"server": SERVER})],
    )
    assert result["changed"] and result["server"] == SERVER
    assert requests[1][1].endswith("/images/image-id")
    assert requests[-1][0] == "POST"
    assert requests[-1][3] == {
        "name": "algo",
        **CREATE,
        "tags": ["Environment:Algo"],
        "enable_ipv6": True,
        "dynamic_ip_required": True,
        "boot_type": "local",
    }


@pytest.mark.parametrize("image", [None, [], {}, {"id": "wrong"}, "malformed"])
def test_reject_invalid_image_before_creating(run_instance, image):
    result, requests = run_instance(CREATE, [(200, {"servers": []}), (200, {"image": image})])
    assert result["failed"] and "cannot read image image-id" in result["msg"]
    assert all(request[0] == "GET" for request in requests)


def test_existing_instance_is_idempotent_without_image_lookup(run_instance):
    result, requests = run_instance(CREATE, [(200, {"servers": [SERVER]})])
    assert result["changed"] is False
    assert len(requests) == 1


def test_update_tags(run_instance):
    updated = dict(SERVER, tags=["Environment:Algo"])
    result, requests = run_instance(
        {**CREATE, "tags": updated["tags"]},
        [(200, {"servers": [SERVER]}), (200, {"server": updated})],
    )
    assert result["changed"] and result["server"] == updated
    assert requests[-1][0] == "PATCH" and requests[-1][3] == {"tags": updated["tags"]}


def test_search_paginates_and_matches_exact_name(run_instance):
    first_page = [dict(SERVER, id=str(i), name=f"algo-{i}") for i in range(100)]
    result, requests = run_instance(
        CREATE,
        [(200, {"servers": first_page}), (200, {"servers": [SERVER]})],
    )
    assert result["server"]["id"] == "server-id" and not result["changed"]
    assert [request[2]["page"] for request in requests] == [["1"], ["2"]]


def test_refuse_ambiguous_names(run_instance):
    result, requests = run_instance(
        {"state": "absent"},
        [(200, {"servers": [SERVER, dict(SERVER, id="other")]})],
    )
    assert result["failed"] and "multiple servers" in result["msg"]
    assert len(requests) == 1


def test_start_waits_for_action_and_returns_latest_address(run_instance):
    running = dict(SERVER, state="running", public_ips=[{"family": "inet", "address": "192.0.2.1"}])
    result, requests = run_instance(
        {"state": "running"},
        [
            (200, {"servers": [SERVER]}),
            (202, {"task": {}}),
            (200, {"server": SERVER}),
            (200, {"server": dict(SERVER, state="starting")}),
            (200, {"server": running}),
        ],
    )
    assert result["changed"] and result["server"]["public_ips"][0]["address"] == "192.0.2.1"
    assert requests[1][3] == {"action": "poweron"}


def test_running_instance_is_idempotent(run_instance):
    running = dict(SERVER, state="running")
    result, requests = run_instance({"state": "running"}, [(200, {"servers": [running]})])
    assert not result["changed"] and result["server"] == running
    assert len(requests) == 1


def test_delete_needs_no_image_or_creation_arguments(run_instance):
    running = dict(SERVER, state="running")
    result, requests = run_instance(
        {"state": "absent"},
        [
            (200, {"servers": [running]}),
            (202, {"task": {}}),
            (200, {"server": dict(SERVER, state="stopping")}),
            (200, {"server": SERVER}),
            (204, None),
        ],
    )
    assert result["changed"] and result["server"] == {}
    assert requests[1][3] == {"action": "poweroff"}
    assert requests[-1][0] == "DELETE"
    assert all("/images/" not in request[1] for request in requests)


def test_absent_instance_is_idempotent(run_instance):
    result, requests = run_instance({"state": "absent"}, [(200, {"servers": []})])
    assert not result["changed"] and result["server"] == {}
    assert len(requests) == 1


@pytest.mark.parametrize("state", ["present", "running", "absent"])
def test_check_mode_never_writes(run_instance, state):
    result, requests = run_instance(
        {**CREATE, "state": state, "tags": ["new-tag"], "_ansible_check_mode": True},
        [(200, {"servers": [SERVER]})],
    )
    assert result["changed"]
    assert all(request[0] == "GET" for request in requests)


@pytest.mark.parametrize(
    "response, message",
    [
        ((401, {}), "HTTP 401"),
        ((500, {}), "HTTP 500"),
        ((-1, None), "HTTP -1"),
        ((200, b"invalid"), "invalid JSON"),
        ((200, []), "no JSON object"),
        ((200, {}), "invalid list"),
        ((200, {"servers": [None]}), "invalid list"),
        ((200, {"servers": [{"name": "algo"}]}), "no server ID"),
    ],
)
def test_api_failures_are_actionable(run_instance, response, message):
    result, _requests = run_instance({"state": "absent"}, [response])
    assert result["failed"] and message in result["msg"]
    assert "algo in nl-ams-2" in result["msg"]


@pytest.mark.parametrize(
    "servers, message",
    [([], "does not exist"), ([dict(SERVER, state="locked")], "unexpected state")],
)
def test_cannot_start_missing_or_locked_instance(run_instance, servers, message):
    result, _requests = run_instance({"state": "running"}, [(200, {"servers": servers})])
    assert result["failed"] and message in result["msg"]


def test_transition_timeout(run_instance, monkeypatch):
    ticks = iter([0, 0, 0, 0, 2])
    monkeypatch.setattr(scaleway_instance.time, "monotonic", lambda: next(ticks))
    server = dict(SERVER, state="starting")
    result, _requests = run_instance(
        {"state": "running", "wait_timeout": 1},
        [(200, {"servers": [server]}), (200, {"server": server})],
    )
    assert result["failed"] and "transition timed out" in result["msg"]


@pytest.mark.parametrize("arguments", [{"name": ""}, {"wait_timeout": 0}, {"wait_timeout": -1}])
def test_invalid_arguments_fail_before_http(run_instance, arguments):
    result, requests = run_instance({"state": "absent", **arguments}, [])
    assert result["failed"] and "positive wait_timeout" in result["msg"]
    assert requests == []


def test_search_timeout(run_instance, monkeypatch):
    ticks = iter([0, 0, 2])
    monkeypatch.setattr(scaleway_instance.time, "monotonic", lambda: next(ticks))
    servers = [dict(SERVER, name=f"other-{index}") for index in range(100)]
    result, _requests = run_instance(
        {"state": "absent", "wait_timeout": 1},
        [(200, {"servers": servers})],
    )
    assert result["failed"] and "listing servers timed out" in result["msg"]


@pytest.mark.parametrize(
    "response",
    [(200, None), (200, b"\xff"), (200, {"servers": [dict(SERVER, id="")]})],
)
def test_malformed_api_payloads_fail(run_instance, response):
    result, requests = run_instance({"state": "absent"}, [response])
    assert result["failed"] and len(requests) == 1


def test_concurrent_deletion_is_idempotent(run_instance):
    result, requests = run_instance(
        {"state": "absent"},
        [(200, {"servers": [SERVER]}), (404, {})],
    )
    assert result["changed"] and requests[-1][0] == "DELETE"


def test_check_mode_does_not_create_instance(run_instance):
    result, requests = run_instance(
        {**CREATE, "_ansible_check_mode": True},
        [(200, {"servers": []})],
    )
    assert result["changed"] and len(requests) == 1


def test_create_waits_for_pending_instance(run_instance):
    result, _requests = run_instance(
        CREATE,
        [
            (200, {"servers": []}),
            (200, {"image": {"id": "image-id"}}),
            (201, {"server": dict(SERVER, state="pending")}),
            (200, {"server": SERVER}),
        ],
    )
    assert result["changed"] and result["server"]["state"] == "stopped"


def test_power_action_rejects_locked_state(run_instance):
    result, _requests = run_instance(
        {"state": "running"},
        [
            (200, {"servers": [SERVER]}),
            (202, {"task": {}}),
            (200, {"server": dict(SERVER, state="locked")}),
        ],
    )
    assert result["failed"] and "unexpected state 'locked'" in result["msg"]


@pytest.mark.parametrize("state", [None, {}, []])
def test_malformed_state_fails_clearly(run_instance, state):
    result, _requests = run_instance(
        {"state": "running"},
        [(200, {"servers": [dict(SERVER, state=state)]})],
    )
    assert result["failed"] and "invalid state" in result["msg"]


def test_existing_instance_gets_public_ipv4(run_instance):
    result, requests = run_instance(
        CREATE,
        [
            (200, {"servers": [dict(SERVER, dynamic_ip_required=False)]}),
            (200, {"server": SERVER}),
        ],
    )
    assert result["changed"]
    assert requests[-1][3] == {"dynamic_ip_required": True}
