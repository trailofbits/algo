"""
Test to detect double Jinja2 templating issues in YAML files.

This test prevents Ansible 12+ errors from embedded templates in Jinja2 expressions.
The pattern `{{ lookup('file', '{{ var }}') }}` is invalid and must be
`{{ lookup('file', var) }}` instead.

Issue: https://github.com/trailofbits/algo/issues/14835
"""

import re
from pathlib import Path

import pytest


def find_yaml_files() -> list[Path]:
    """Find all YAML files in the repository."""
    repo_root = Path(__file__).parent.parent.parent
    yaml_files = []

    # Include all .yml and .yaml files
    for pattern in ["**/*.yml", "**/*.yaml"]:
        yaml_files.extend(repo_root.glob(pattern))

    # Exclude test files and vendor directories
    excluded_dirs = {"venv", ".venv", "env", ".git", "__pycache__", ".pytest_cache"}
    yaml_files = [f for f in yaml_files if not any(excluded in f.parts for excluded in excluded_dirs)]

    return sorted(yaml_files)


def detect_double_templating(content: str) -> list[tuple[int, str]]:
    """
    Detect double templating patterns in file content.

    Returns list of (line_number, problematic_line) tuples.
    """
    issues = []

    # Pattern 1: lookup() with embedded {{ }}
    # Matches: lookup('file', '{{ var }}') or lookup("file", "{{ var }}")
    pattern1 = r"lookup\s*\([^)]*['\"]{{[^}]*}}['\"][^)]*\)"

    # Pattern 2: Direct nested {{ {{ }} }}
    pattern2 = r"{{\s*[^}]*{{\s*[^}]*}}"

    # Pattern 3: Embedded templates in quoted strings within Jinja2
    # This catches cases like value: "{{ '{{ var }}' }}"
    pattern3 = r"{{\s*['\"][^'\"]*{{[^}]*}}[^'\"]*['\"]"

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.split("#")[0]
        if not stripped.strip():
            continue

        if re.search(pattern1, stripped) or re.search(pattern2, stripped) or re.search(pattern3, stripped):
            issues.append((i, line))

    return issues


def test_no_double_templating():
    """Test that no YAML files contain double templating patterns."""
    yaml_files = find_yaml_files()
    all_issues = {}

    for yaml_file in yaml_files:
        try:
            content = yaml_file.read_text()
            issues = detect_double_templating(content)
            if issues:
                # Store relative path for cleaner output
                rel_path = yaml_file.relative_to(Path(__file__).parent.parent.parent)
                all_issues[str(rel_path)] = issues
        except Exception:
            # Skip binary files or files we can't read
            continue

    if all_issues:
        # Format error message for clarity
        error_msg = "\n\nDouble templating issues found:\n"
        error_msg += "=" * 60 + "\n"

        for file_path, issues in all_issues.items():
            error_msg += f"\n{file_path}:\n"
            for line_num, line in issues:
                error_msg += f"  Line {line_num}: {line.strip()}\n"

        error_msg += "\n" + "=" * 60 + "\n"
        error_msg += "Fix: Replace '{{ var }}' with var inside lookup() calls\n"
        error_msg += "Example: lookup('file', '{{ SSH_keys.public }}') → lookup('file', SSH_keys.public)\n"

        pytest.fail(error_msg)


def test_specific_known_issues():
    """
    Test for specific known double-templating issues.
    This ensures our detection catches the actual bugs from issue #14835.
    """
    # These are the actual problematic patterns from the codebase
    known_bad_patterns = [
        "{{ lookup('file', '{{ SSH_keys.public }}') }}",
        '{{ lookup("file", "{{ credentials_file_path }}") }}',
        "value: \"{{ lookup('file', '{{ SSH_keys.public }}') }}\"",
        "PayloadContentCA: \"{{ lookup('file' , '{{ ipsec_pki_path }}/cacert.pem')|b64encode }}\"",
    ]

    for pattern in known_bad_patterns:
        issues = detect_double_templating(pattern)
        assert issues, f"Failed to detect known bad pattern: {pattern}"


def test_valid_patterns_not_flagged():
    """
    Test that valid templating patterns are not flagged as errors.
    """
    valid_patterns = [
        "{{ lookup('file', SSH_keys.public) }}",
        "{{ lookup('file', credentials_file_path) }}",
        "value: \"{{ lookup('file', SSH_keys.public) }}\"",
        "{{ item.1 }}.mobileconfig",
        "{{ loop.index }}. {{ r.server }} ({{ r.IP_subject_alt_name }})",
        "PayloadContentCA: \"{{ lookup('file', ipsec_pki_path + '/cacert.pem')|b64encode }}\"",
        "ssh_pub_key: \"{{ lookup('file', SSH_keys.public) }}\"",
    ]

    for pattern in valid_patterns:
        issues = detect_double_templating(pattern)
        assert not issues, f"Valid pattern incorrectly flagged: {pattern}"


if __name__ == "__main__":
    # Run the test directly for debugging
    test_specific_known_issues()
    test_valid_patterns_not_flagged()
    test_no_double_templating()
    print("All tests passed!")
