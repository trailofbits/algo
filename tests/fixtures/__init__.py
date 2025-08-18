"""Test fixtures for Algo unit tests"""

from pathlib import Path

import yaml


def load_test_variables():
    """Load test variables from YAML fixture"""
    fixture_path = Path(__file__).parent / "test_variables.yml"
    with open(fixture_path) as f:
        return yaml.safe_load(f)


def get_test_config(overrides=None):
    """Get test configuration with optional overrides"""
    config = load_test_variables()
    if overrides:
        config.update(overrides)
    return config
