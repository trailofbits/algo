# Development Guide

This guide covers the development setup and best practices for contributing to Algo.

## Prerequisites

- Python 3.11 or higher
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git

## Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/trailofbits/algo.git
   cd algo
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync --dev
   ```

3. **Install Ansible collections**
   ```bash
   uv run ansible-galaxy install -r requirements.yml
   ```

4. **Set up pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

## Pre-commit Hooks

This project uses pre-commit hooks to maintain code quality. The hooks run automatically before each commit to catch issues early.

### What Gets Checked

- **Python code** (via ruff): Style, imports, common errors
- **YAML files** (via yamllint): Syntax and formatting
- **Shell scripts** (via shellcheck): Common bash issues
- **Ansible playbooks** (via ansible-lint): Best practices and syntax
- **General**: Trailing whitespace, file endings, merge conflicts

### Manual Testing

To run pre-commit on all files:
```bash
uv run pre-commit run --all-files
```

To run on specific files:
```bash
uv run pre-commit run --files path/to/file.yml
```

To skip hooks temporarily (not recommended):
```bash
git commit --no-verify -m "your message"
```

### Updating Hooks

To update pre-commit hooks to their latest versions:
```bash
uv run pre-commit autoupdate
```

## Running Linters Manually

If you need to run linters outside of pre-commit:

```bash
# Python linting
uv run ruff check .
uv run ruff format .

# YAML linting
uv run yamllint .

# Ansible linting
uv run ansible-lint

# Shell script linting
shellcheck scripts/*.sh

# Run all linters (CI simulation)
./scripts/lint.sh
```

## Testing

Run unit tests:
```bash
uv run pytest tests/unit/
```

Check playbook syntax:
```bash
uv run ansible-playbook main.yml --syntax-check
```

## Before Pushing Code

1. **Pre-commit hooks will run automatically** when you commit
2. **Fix any issues** reported by the hooks
3. **Run tests** to ensure nothing is broken
4. **Update documentation** if you've added new features

## Troubleshooting

### Pre-commit Hook Failures

If a pre-commit hook fails:
1. Read the error message carefully
2. Fix the issue in your code
3. Stage the fixes: `git add .`
4. Try committing again

### Common Issues

- **ansible-lint fails**: Ensure Ansible collections are installed
- **yamllint fails**: Check `.yamllint` for configuration rules
- **ruff fails**: Run `uv run ruff format` to auto-fix most issues

## Additional Resources

- [Pre-commit documentation](https://pre-commit.com/)
- [Ansible-lint rules](https://ansible.readthedocs.io/projects/lint/)
- [Ruff rules](https://docs.astral.sh/ruff/rules/)
- [YAMLlint rules](https://yamllint.readthedocs.io/)
