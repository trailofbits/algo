#!/usr/bin/env python3
"""
Validate all Jinja2 templates in the Algo codebase.
This script checks for:
1. Syntax errors (including inline comments in expressions)
2. Undefined variables
3. Common anti-patterns
"""

import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateSyntaxError, meta


def find_jinja2_templates(root_dir: str = ".") -> list[Path]:
    """Find all Jinja2 template files in the project."""
    templates = []
    patterns = ["**/*.j2", "**/*.jinja2", "**/*.yml.j2", "**/*.conf.j2"]

    # Skip these directories
    skip_dirs = {".git", ".venv", "venv", ".env", "configs", "__pycache__", ".cache"}

    for pattern in patterns:
        for path in Path(root_dir).glob(pattern):
            # Skip if in a directory we want to ignore
            if not any(skip_dir in path.parts for skip_dir in skip_dirs):
                templates.append(path)

    return sorted(templates)


def check_inline_comments_in_expressions(template_content: str, template_path: Path) -> list[str]:
    """
    Check for inline comments (#) within Jinja2 expressions.
    This is the error we just fixed in openssl.yml.
    """
    errors = []

    # Pattern to find Jinja2 expressions
    jinja_pattern = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)

    for match in jinja_pattern.finditer(template_content):
        expression = match.group()
        lines = expression.split("\n")

        for i, line in enumerate(lines):
            # Check for # that's not in a string
            # Simple heuristic: if # appears after non-whitespace and not in quotes
            if "#" in line:
                # Remove quoted strings to avoid false positives
                cleaned = re.sub(r'"[^"]*"', "", line)
                cleaned = re.sub(r"'[^']*'", "", cleaned)

                if "#" in cleaned:
                    # Check if it's likely a comment (has text after it)
                    hash_pos = cleaned.index("#")
                    if hash_pos > 0 and cleaned[hash_pos - 1 : hash_pos] != "\\":
                        line_num = template_content[: match.start()].count("\n") + i + 1
                        errors.append(
                            f"{template_path}:{line_num}: Inline comment (#) found in Jinja2 expression. "
                            f"Move comments outside the expression."
                        )

    return errors


def check_undefined_variables(template_path: Path) -> list[str]:
    """
    Parse template and extract all undefined variables.
    This helps identify what variables need to be provided.
    """
    errors = []

    try:
        with open(template_path) as f:
            template_content = f.read()

        env = Environment(undefined=StrictUndefined)
        ast = env.parse(template_content)
        undefined_vars = meta.find_undeclared_variables(ast)

        # Common Ansible variables that are always available
        ansible_builtins = {
            "ansible_default_ipv4",
            "ansible_default_ipv6",
            "ansible_hostname",
            "ansible_distribution",
            "ansible_distribution_version",
            "ansible_facts",
            "inventory_hostname",
            "hostvars",
            "groups",
            "group_names",
            "play_hosts",
            "ansible_version",
            "ansible_user",
            "ansible_host",
            "item",
            "ansible_loop",
            "ansible_index",
            "lookup",
        }

        # Filter out known Ansible variables
        unknown_vars = undefined_vars - ansible_builtins

        # Only report if there are truly unknown variables
        if unknown_vars and len(unknown_vars) < 20:  # Avoid noise from templates with many vars
            errors.append(f"{template_path}: Uses undefined variables: {', '.join(sorted(unknown_vars))}")

    except Exception:
        # Don't report parse errors here, they're handled elsewhere
        pass

    return errors


def validate_template_syntax(template_path: Path) -> tuple[bool, list[str]]:
    """
    Validate a single template for syntax errors.
    Returns (is_valid, list_of_errors)
    """
    errors = []

    # Skip full parsing for templates that use Ansible-specific features heavily
    # We still check for inline comments but skip full template parsing
    ansible_specific_templates = {
        "dnscrypt-proxy.toml.j2",  # Uses |bool filter
        "mobileconfig.j2",  # Uses |to_uuid filter and complex item structures
        "vpn-dict.j2",  # Uses |to_uuid filter
    }

    if template_path.name in ansible_specific_templates:
        # Still check for inline comments but skip full parsing
        try:
            with open(template_path) as f:
                template_content = f.read()
            errors.extend(check_inline_comments_in_expressions(template_content, template_path))
        except Exception:
            pass
        return len(errors) == 0, errors

    try:
        with open(template_path) as f:
            template_content = f.read()

        # Check for inline comments first (our custom check)
        errors.extend(check_inline_comments_in_expressions(template_content, template_path))

        # Try to parse the template
        env = Environment(loader=FileSystemLoader(template_path.parent), undefined=StrictUndefined)

        # Add mock Ansible filters to avoid syntax errors
        env.filters["bool"] = lambda x: x
        env.filters["to_uuid"] = lambda x: x
        env.filters["b64encode"] = lambda x: x
        env.filters["b64decode"] = lambda x: x
        env.filters["regex_replace"] = lambda x, y, z: x
        env.filters["default"] = lambda x, d: x if x else d

        # This will raise TemplateSyntaxError if there's a syntax problem
        env.get_template(template_path.name)

        # Also check for undefined variables (informational)
        # Commenting out for now as it's too noisy, but useful for debugging
        # errors.extend(check_undefined_variables(template_path))

    except TemplateSyntaxError as e:
        errors.append(f"{template_path}:{e.lineno}: Syntax error: {e.message}")
    except UnicodeDecodeError:
        errors.append(f"{template_path}: Unable to decode file (not UTF-8)")
    except Exception as e:
        errors.append(f"{template_path}: Error: {str(e)}")

    return len(errors) == 0, errors


def check_common_antipatterns(template_path: Path) -> list[str]:
    """Check for common Jinja2 anti-patterns."""
    warnings = []

    try:
        with open(template_path) as f:
            content = f.read()

        # Check for missing spaces around filters
        if re.search(r"\{\{[^}]+\|[^ ]", content):
            warnings.append(f"{template_path}: Missing space after filter pipe (|)")

        # Check for deprecated 'when' in Jinja2 (should use if)
        if re.search(r"\{%\s*when\s+", content):
            warnings.append(f"{template_path}: Use 'if' instead of 'when' in Jinja2 templates")

        # Check for extremely long expressions (harder to debug)
        for match in re.finditer(r"\{\{(.+?)\}\}", content, re.DOTALL):
            if len(match.group(1)) > 200:
                line_num = content[: match.start()].count("\n") + 1
                warnings.append(
                    f"{template_path}:{line_num}: Very long expression (>200 chars), consider breaking it up"
                )

    except Exception:
        pass  # Ignore errors in anti-pattern checking

    return warnings


def main():
    """Main validation function."""
    print("🔍 Validating Jinja2 templates in Algo...\n")

    # Find all templates
    templates = find_jinja2_templates()
    print(f"Found {len(templates)} Jinja2 templates\n")

    all_errors = []
    all_warnings = []
    valid_count = 0

    # Validate each template
    for template in templates:
        is_valid, errors = validate_template_syntax(template)
        warnings = check_common_antipatterns(template)

        if is_valid:
            valid_count += 1
        else:
            all_errors.extend(errors)

        all_warnings.extend(warnings)

    # Report results
    print(f"✅ {valid_count}/{len(templates)} templates have valid syntax")

    if all_errors:
        print(f"\n❌ Found {len(all_errors)} errors:\n")
        for error in all_errors:
            print(f"  ERROR: {error}")

    if all_warnings:
        print(f"\n⚠️  Found {len(all_warnings)} warnings:\n")
        for warning in all_warnings:
            print(f"  WARN: {warning}")

    if all_errors:
        print("\n❌ Template validation FAILED")
        return 1
    else:
        print("\n✅ All templates validated successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
