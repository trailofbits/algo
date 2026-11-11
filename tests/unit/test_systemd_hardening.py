#!/usr/bin/env python3
"""
Tests for the systemd hardening drop-ins the roles install.
"""

import re
from pathlib import Path

PATH_DIRECTIVE = re.compile(r"^\s*(ReadOnlyPaths|ReadWritePaths|InaccessiblePaths)=(.*)$")


def find_path_directives():
    """Yield (file, line number, directive, entry) for every sandbox path in role templates and tasks"""
    files = [*Path("roles").glob("*/templates/**/*"), *Path("roles").glob("*/tasks/*.yml")]
    for path in filter(Path.is_file, files):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            match = PATH_DIRECTIVE.match(line)
            if match:
                for entry in match.group(2).split():
                    yield path, number, match.group(1), entry


def test_kernel_paths_are_optional():
    """/proc and /sys entries depend on the running kernel and loaded modules (e.g. /proc/net/pfkey
    only exists while af_key is loaded). Without the "-" prefix systemd refuses to start the unit
    with 226/NAMESPACE when the path is missing."""
    directives = list(find_path_directives())
    assert directives, "no systemd sandbox path directives found"

    errors = [
        f"{path}:{number}: {directive}={entry} must be written as {directive}=-{entry}"
        for path, number, directive, entry in directives
        if entry.startswith(("/proc/", "/sys/"))
    ]
    assert not errors, "\n".join(errors)
