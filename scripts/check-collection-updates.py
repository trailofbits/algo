#!/usr/bin/env python3
"""Report stable Ansible Galaxy collection updates without modifying the repository."""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
from collections.abc import Callable, Iterable
from http.client import HTTPSConnection
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import yaml
from packaging.version import InvalidVersion, Version

GALAXY_API_ROOT = "https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/"
EXACT_VERSION = re.compile(r"^==(?P<version>[^\s*]+)$")


def load_collection_pins(path: Path) -> dict[str, str]:
    """Load unique exact collection pins from an Ansible requirements file."""
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("collections"), list):
        raise ValueError(f"{path} must contain a collections list")

    pins: dict[str, str] = {}
    for item in document["collections"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("every collection must declare a string name")
        name = item["name"].casefold()
        version_specifier = item.get("version")
        match = EXACT_VERSION.fullmatch(version_specifier) if isinstance(version_specifier, str) else None
        if match is None:
            raise ValueError(f"{name} must use one exact == version")
        if name in pins:
            raise ValueError(f"duplicate collection: {name}")
        version = match.group("version")
        try:
            Version(version)
        except InvalidVersion as error:
            raise ValueError(f"{name} has invalid version {version}") from error
        pins[name] = version
    return pins


def _page_versions(payload: Any) -> tuple[list[str], str | None]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("Galaxy response does not contain a data list")
    versions: list[str] = []
    for item in payload["data"]:
        if isinstance(item, dict) and isinstance(item.get("version"), str):
            versions.append(item["version"])
    links = payload.get("links")
    next_page = links.get("next") if isinstance(links, dict) else None
    return versions, next_page if isinstance(next_page, str) and next_page else None


def validated_next_url(next_page: str) -> str:
    """Resolve Galaxy pagination while refusing cross-origin redirects."""
    resolved = urljoin("https://galaxy.ansible.com/", next_page)
    parsed = urlparse(resolved)
    if parsed.scheme != "https" or parsed.netloc != "galaxy.ansible.com":
        raise ValueError("Galaxy pagination URL points outside galaxy.ansible.com")
    return resolved


def _fetch_galaxy_payload(url: str) -> Any:
    """Fetch JSON from the fixed Galaxy HTTPS origin without dynamic URL schemes."""
    parsed = urlparse(validated_next_url(url))
    target = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    # Python >=3.12 plus an explicit default context verifies the fixed Galaxy host.
    connection = HTTPSConnection(  # nosemgrep
        "galaxy.ansible.com",
        timeout=30,
        context=ssl.create_default_context(),
    )
    try:
        connection.request(
            "GET",
            target,
            headers={"Accept": "application/json", "User-Agent": "algo-collection-update-checker"},
        )
        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError(f"Galaxy returned HTTP {response.status}")
        return json.loads(response.read())
    finally:
        connection.close()


def fetch_galaxy_versions(name: str) -> list[str]:
    """Fetch all published versions for one namespace.collection name."""
    try:
        namespace, collection = name.split(".", maxsplit=1)
    except ValueError as error:
        raise ValueError(f"invalid collection name: {name}") from error

    url: str | None = f"{GALAXY_API_ROOT}{quote(namespace, safe='')}/{quote(collection, safe='')}/versions/?limit=100"
    versions: list[str] = []
    while url is not None:
        payload = _fetch_galaxy_payload(url)
        page_versions, next_page = _page_versions(payload)
        versions.extend(page_versions)
        url = validated_next_url(next_page) if next_page else None
    return versions


def find_updates(
    pins: dict[str, str],
    *,
    fetch_versions: Callable[[str], Iterable[str]],
    excluded: set[str],
) -> list[tuple[str, str, str]]:
    """Return stable collection updates sorted by collection name."""
    normalized_exclusions = {name.casefold() for name in excluded}
    updates: list[tuple[str, str, str]] = []
    for name, pinned_text in sorted(pins.items()):
        if name.casefold() in normalized_exclusions:
            continue
        pinned = Version(pinned_text)
        available: list[Version] = []
        for candidate in fetch_versions(name):
            try:
                parsed = Version(candidate)
            except InvalidVersion:
                continue
            if not parsed.is_prerelease and not parsed.is_devrelease:
                available.append(parsed)
        if not available:
            raise ValueError(f"Galaxy returned no stable versions for {name}")
        latest = max(available)
        if latest > pinned:
            updates.append((name, pinned_text, str(latest)))
    return updates


def render_report(updates: list[tuple[str, str, str]], *, excluded: set[str]) -> str:
    """Render a deterministic Markdown report for the workflow summary."""
    lines = ["## Ansible collection update report", ""]
    if updates:
        lines.extend(["| Collection | Pinned | Latest stable |", "|---|---:|---:|"])
        lines.extend(f"| `{name}` | `{pinned}` | `{latest}` |" for name, pinned, latest in updates)
    else:
        lines.append("All checked collections use the latest stable version.")
    if excluded:
        exclusions = ", ".join(f"`{name}`" for name in sorted(name.casefold() for name in excluded))
        lines.extend(["", f"Excluded by maintenance scope: {exclusions}."])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, default=Path("requirements.yml"))
    parser.add_argument("--exclude", action="append", default=[], metavar="NAMESPACE.COLLECTION")
    parser.add_argument("--output", type=Path, help="write Markdown to this file instead of stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pins = load_collection_pins(args.requirements)
    excluded = {name.casefold() for name in args.exclude}
    updates = find_updates(pins, fetch_versions=fetch_galaxy_versions, excluded=excluded)
    report = render_report(updates, excluded=excluded)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
