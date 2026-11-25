"""Exercise Google collection pagination and the location module's response handling."""

import json
from unittest.mock import Mock

import pytest
from ansible.module_utils import basic


@pytest.mark.parametrize("scenario", ["pages", "empty", "missing", "invalid", "api-error"])
def test_location_response(monkeypatch, capsys, scenario):
    import gcp_compute_location_info as locations

    arguments = {
        "project": "sample",
        "auth_kind": "machineaccount",
        "scope": "zones",
        "filters": ["name=eu-*", "status=UP"],
    }
    monkeypatch.setattr(basic, "_ANSIBLE_ARGS", json.dumps({"ANSIBLE_MODULE_ARGS": arguments}).encode())
    monkeypatch.setattr(basic, "_ANSIBLE_PROFILE", "legacy")
    pages = [{"items": [{"name": "a"}], "nextPageToken": "next"}, {"items": [{"name": "b"}]}]
    requests = []

    def get(_self, url, params):
        requests.append((url, params.copy()))
        response = Mock(status_code={"empty": 204, "missing": 404}.get(scenario, 200))
        if scenario == "invalid":
            response.json.side_effect = ValueError("invalid document")
        elif scenario == "api-error":
            response.json.return_value = {"error": {"message": "permission denied"}}
        elif scenario == "pages":
            response.json.return_value = pages.pop(0)
        return response

    monkeypatch.setattr(locations.GcpSession, "full_get", get)
    # GcpSession checks optional SDK imports before issuing a request.
    pytest.importorskip("google.auth", reason="Install the gcp extra")
    with pytest.raises(SystemExit) as status:
        locations.main()
    result = json.loads(capsys.readouterr().out)
    if scenario in {"invalid", "api-error"}:
        assert status.value.code == 1 and (
            "invalid" in str(result["msg"]).lower() or "permission denied" in str(result["msg"])
        )
    else:
        assert status.value.code == 0, result
        assert result["resources"] == ([{"name": "a"}, {"name": "b"}] if scenario == "pages" else [])
    assert requests[0] == (
        "https://compute.googleapis.com/compute/v1/projects/sample/zones",
        {"filter": "(name=eu-*) (status=UP)"},
    )
    if scenario == "pages":
        assert requests[1][1]["pageToken"] == "next"
