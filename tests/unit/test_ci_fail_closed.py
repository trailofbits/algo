"""CI policy regression tests: validation must run broadly and fail closed."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
VALIDATION_WORKFLOWS = ("main.yml", "lint.yml", "smart-tests.yml")


def _load_workflow(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _triggers(workflow):
    return workflow.get("on", workflow.get(True, {}))


def test_validation_workflows_cover_push_pull_request_and_manual_runs():
    for name in VALIDATION_WORKFLOWS:
        assert {"push", "pull_request", "workflow_dispatch"} <= set(_triggers(_load_workflow(name))), name


def test_pull_requests_run_the_complete_pytest_suite():
    workflow = _load_workflow("main.yml")
    steps = workflow["jobs"]["basic-tests"]["steps"]
    pytest_steps = [step for step in steps if "pytest" in step.get("run", "")]

    assert len(pytest_steps) == 1
    assert pytest_steps[0]["run"].strip() == "uv run pytest -v"


def test_validation_commands_do_not_mask_failures():
    paths = [WORKFLOWS / name for name in VALIDATION_WORKFLOWS] + [ROOT / "scripts" / "lint.sh"]
    fail_open = re.compile(r"\|\|\s*(?:true|echo\b)|continue-on-error\s*:\s*true")

    offenders = [str(path.relative_to(ROOT)) for path in paths if fail_open.search(path.read_text(encoding="utf-8"))]
    assert offenders == []


def test_actionlint_checks_both_workflow_extensions():
    workflow = _load_workflow("lint.yml")
    step = next(step for step in workflow["jobs"]["actionlint"]["steps"] if step.get("name") == "Run actionlint")
    assert step["run"].strip() == "actionlint .github/workflows/*.yml .github/workflows/*.yaml"


def test_shellcheck_aggregates_all_repository_script_failures():
    workflow = _load_workflow("lint.yml")
    step = next(step for step in workflow["jobs"]["shellcheck"]["steps"] if step.get("name") == "Run shellcheck")
    command = step["run"]

    assert "-print0" in command
    assert "xargs -0 --no-run-if-empty shellcheck" in command
    assert '"./.venv/*"' in command
    assert '"./.ansible/*"' in command
    assert "-exec shellcheck" not in command
