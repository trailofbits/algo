"""Tests for report-only Ansible collection update checks."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/check-collection-updates.py"


def _load_checker():
    assert SCRIPT.is_file(), "scripts/check-collection-updates.py must exist"
    spec = importlib.util.spec_from_file_location("check_collection_updates", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_collection_pins_rejects_non_exact_versions(tmp_path):
    checker = _load_checker()
    requirements = tmp_path / "requirements.yml"
    requirements.write_text(
        "---\ncollections:\n  - name: amazon.aws\n    version: '>=11.0.0'\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="exact == version"):
        checker.load_collection_pins(requirements)


def test_find_updates_reports_latest_stable_and_excludes_requested_collection():
    checker = _load_checker()
    pins = {
        "amazon.aws": "11.4.0",
        "azure.azcollection": "3.21.0",
        "google.cloud": "1.14.0",
    }
    available = {
        "amazon.aws": ["12.0.0rc1", "11.5.0", "11.4.0"],
        "azure.azcollection": ["3.22.0"],
        "google.cloud": ["1.14.0"],
    }

    updates = checker.find_updates(
        pins,
        fetch_versions=lambda name: available[name],
        excluded={"azure.azcollection"},
    )

    assert updates == [("amazon.aws", "11.4.0", "11.5.0")]


def test_render_report_is_deterministic_and_marks_exclusions():
    checker = _load_checker()

    report = checker.render_report(
        [("amazon.aws", "11.4.0", "11.5.0")],
        excluded={"azure.azcollection"},
    )

    assert report == (
        "## Ansible collection update report\n\n"
        "| Collection | Pinned | Latest stable |\n"
        "|---|---:|---:|\n"
        "| `amazon.aws` | `11.4.0` | `11.5.0` |\n\n"
        "Excluded by maintenance scope: `azure.azcollection`.\n"
    )


def test_galaxy_pagination_rejects_external_urls():
    checker = _load_checker()

    with pytest.raises(ValueError, match=r"outside galaxy\.ansible\.com"):
        checker.validated_next_url("https://example.com/collect")

    assert checker.validated_next_url("/api/v3/next-page") == "https://galaxy.ansible.com/api/v3/next-page"
