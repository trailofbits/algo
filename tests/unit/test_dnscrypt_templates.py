"""Regression tests for dnscrypt-proxy source template rendering."""

import tomllib
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parents[2]
TEMPLATE_DIR = ROOT / "roles/dns/templates/dnscrypt-proxy"


def render_sources(custom_server_stamps):
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        undefined=StrictUndefined,
        trim_blocks=True,
        keep_trailing_newline=True,
    )
    return env.get_template("sources.toml.j2").render(custom_server_stamps=custom_server_stamps)


@pytest.mark.parametrize(
    "stamps",
    [
        {},
        {"v4": "stamp4"},
        {"v4": "stamp4", "v6": "stamp6"},
    ],
)
def test_custom_server_stamps_render_as_distinct_valid_toml_tables(stamps):
    output = render_sources(stamps)
    parsed = tomllib.loads(output)

    assert "sources" in parsed
    assert parsed.get("static", {}) == {name: {"stamp": stamp} for name, stamp in stamps.items()}
