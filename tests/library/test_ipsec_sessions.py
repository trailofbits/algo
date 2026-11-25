"""Check the exact IKE handles selected for revoked device identities."""

import algo_ipsec_sessions
import pytest
from algo_ipsec_sessions import retired_sessions


def test_selects_every_session_for_a_retired_user():
    rows = [
        "ikev2-pubkey[11]: ESTABLISHED 2 hours ago, 192.0.2.1[srv]...192.0.2.2[CN=old]",
        "ikev2-pubkey[14]: REKEYING, 192.0.2.1[srv]...192.0.2.3[old@vpn.algo]",
        "ikev2-pubkey[15]: ESTABLISHED 4s ago, 192.0.2.1[srv]...192.0.2.2[CN=old-phone]",
        "ikev2-pubkey[16]: ESTABLISHED 4s ago, 192.0.2.1[srv]...192.0.2.2[old@other.algo]",
        "other[17]: ESTABLISHED 4s ago, 192.0.2.1[srv]...192.0.2.2[CN=old]",
        "ikev2-pubkey{11}: INSTALLED, TUNNEL",
    ]
    assert retired_sessions("\n".join(rows), ["old"], "vpn.algo") == ["ikev2-pubkey[11]", "ikev2-pubkey[14]"]
    assert retired_sessions("\n".join(rows), [], "vpn.algo") == []


@pytest.mark.parametrize(("check", "stays_active"), [(False, False), (True, False), (False, True)])
def test_module_closes_only_matching_sessions(monkeypatch, check, stays_active):
    active = {"11": "old", "12": "phone"}
    commands = []

    class Result(Exception):
        pass

    class Stroke:
        def __init__(self):
            self.params = {"retired": ["old"], "domain": "vpn.algo"}
            self.check_mode = check

        def get_bin_path(self, name, *, required):
            return name

        def run_command(self, argv, **kwargs):
            commands.append(argv)
            if argv[1] == "status":
                return (
                    0,
                    "\n".join(
                        f"ikev2-pubkey[{number}]: ESTABLISHED, host[srv]...peer[CN={user}]"
                        for number, user in active.items()
                    ),
                    "",
                )
            assert argv == ["ipsec", "down", "ikev2-pubkey[11]"]
            if not stays_active:
                del active["11"]
            return 0, "", ""

        def fail_json(self, **kwargs):
            raise Result(kwargs)

        def exit_json(self, **kwargs):
            raise Result(kwargs)

    monkeypatch.setattr(algo_ipsec_sessions, "AnsibleModule", lambda **kwargs: Stroke())
    with pytest.raises(Result) as result:
        algo_ipsec_sessions.main()
    if stays_active:
        assert "remain active" in result.value.args[0]["msg"]
    else:
        assert result.value.args[0] == {"changed": True, "matched": 1}
    assert "12" in active
    assert ("11" in active) == (check or stays_active)
