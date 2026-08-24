"""Regression tests for fail-closed pytest collection and warning policy."""

import ast
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_pytest_collects_the_complete_test_tree_and_fails_on_warnings():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    configuration = tomllib.loads(text)["tool"]["pytest"]["ini_options"]

    assert configuration["testpaths"] == ["tests"]
    assert configuration["filterwarnings"][0] == "error"
    for exception in configuration["filterwarnings"][1:]:
        assert re.fullmatch(r"ignore:[^:]+:[A-Za-z.]+Warning:[A-Za-z0-9_.]+", exception)
        quoted_exception = f'"{exception}"'
        assert re.search(rf"expires \d{{4}}-\d{{2}}-\d{{2}}[^\n]*\n\s*{re.escape(quoted_exception)}", text)


def test_pytest_tests_do_not_return_results():
    offenders = []
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
                continue
            for statement in node.body:
                for descendant in ast.walk(statement):
                    if (
                        isinstance(descendant, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
                        and descendant is not node
                    ):
                        break
                    if isinstance(descendant, ast.Return) and descendant.value is not None:
                        offenders.append(f"{path.relative_to(ROOT)}:{descendant.lineno}")

    assert offenders == []
