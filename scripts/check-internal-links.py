#!/usr/bin/env python3
"""Fail when tracked Markdown contains a broken repository-local link."""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")
REFERENCE_TARGET = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)")
HTML_HREF = re.compile(r"<a\b[^>]*\bhref=['\"]([^'\"]+)['\"]", re.IGNORECASE)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
HTML_ANCHOR = re.compile(r"<a\s+(?:name|id)=['\"]([^'\"]+)['\"]", re.IGNORECASE)
REMOTE_SCHEMES = {"http", "https", "mailto", "tel", "data"}


def markdown_slug(heading: str) -> str:
    heading = re.sub(r"<[^>]+>", "", heading).strip().lower()
    heading = re.sub(r"[^\w\- ]", "", heading, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", heading).strip("-")


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    counts: Counter[str] = Counter()
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        found.update(HTML_ANCHOR.findall(line))
        match = HEADING.match(line)
        if not match:
            continue
        base = markdown_slug(match.group(1))
        if not base:
            continue
        suffix = counts[base]
        counts[base] += 1
        found.add(base if suffix == 0 else f"{base}-{suffix}")
    return found


def tracked_markdown() -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z", "*.md"], cwd=ROOT, check=True, capture_output=True, text=True)
    return [ROOT / name for name in result.stdout.split("\0") if name]


def check_repository_links() -> list[str]:
    problems: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    for source in tracked_markdown():
        text = source.read_text(encoding="utf-8")
        in_fence = False
        for line_number, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            raw_targets = LINK.findall(line)
            raw_targets.extend(REFERENCE_TARGET.findall(line))
            raw_targets.extend(HTML_HREF.findall(line))
            for raw_target in raw_targets:
                target = raw_target.strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme.lower() in REMOTE_SCHEMES or target.startswith("//") or "{{" in target:
                    continue
                destination = (
                    source
                    if not parsed.path
                    else (
                        ROOT / parsed.path.lstrip("/")
                        if parsed.path.startswith("/")
                        else source.parent / unquote(parsed.path)
                    )
                )
                destination = destination.resolve()
                try:
                    destination.relative_to(ROOT)
                except ValueError:
                    problems.append(f"{source.relative_to(ROOT)}:{line_number}: link escapes repository: {target}")
                    continue
                if not destination.exists():
                    problems.append(f"{source.relative_to(ROOT)}:{line_number}: missing target: {target}")
                    continue
                if parsed.fragment and destination.suffix.lower() == ".md":
                    expected = unquote(parsed.fragment).lower()
                    available = anchor_cache.setdefault(destination, anchors(destination))
                    if expected not in available:
                        problems.append(f"{source.relative_to(ROOT)}:{line_number}: missing anchor: {target}")
    return problems


def main() -> int:
    problems = check_repository_links()
    if problems:
        print("Broken internal Markdown links:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print("Internal Markdown links are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
