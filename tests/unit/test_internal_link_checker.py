"""Negative parser coverage for the repository-local Markdown link checker."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[2]
CHECKER = ROOT / "scripts/check-internal-links.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_internal_links", CHECKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_rejects_broken_reference_and_html_links(tmp_path):
    checker = _load_checker()
    source = tmp_path / "README.md"
    source.write_text(
        "[documentation][missing-reference]\n"
        "[missing-reference]: missing-reference.md\n"
        '<a href="missing-html.html">missing HTML target</a>\n',
        encoding="utf-8",
    )
    checker.__dict__["ROOT"] = tmp_path
    checker.__dict__["tracked_markdown"] = lambda: [source]

    problems = checker.check_repository_links()

    assert any("missing-reference.md" in problem for problem in problems)
    assert any("missing-html.html" in problem for problem in problems)
