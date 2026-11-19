#!./.venv/bin/python
"""Generate Keep-a-Changelog-style entries from Conventional Commit messages.

Usage: python changelog_generator.py --input commits.txt --current-version 1.2.3
Omit --input or pass '-' to read stdin. The suggested bump is major/minor/patch.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

PATTERN = re.compile(
    r"^(?P<type>feat|fix|chore|docs|refactor|perf|test|build|ci|revert)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<description>.+)$",
    re.IGNORECASE,
)
GROUPS = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "revert": "Changed",
    "docs": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "test": "Changed",
    "chore": "Changed",
}


def bump(version, level):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError("current-version must be semantic x.y.z")
    major, minor, patch = map(int, match.groups())
    if level == "major":
        major += 1
        minor = patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def parse(lines):
    grouped = {}
    breaking = []
    ignored = []
    for raw in lines:
        line = raw.strip().lstrip("-* ")
        if not line:
            continue
        match = PATTERN.match(line)
        if not match:
            ignored.append(line)
            continue
        item = match.groupdict()
        entry = f"{item['description']}" + (
            f" ({item['scope']})" if item["scope"] else ""
        )
        grouped.setdefault(GROUPS[item["type"].lower()], []).append(entry)
        if item["bang"] or "BREAKING CHANGE" in line.upper():
            breaking.append(entry)
    level = "major" if breaking else "minor" if grouped.get("Added") else "patch"
    return grouped, breaking, ignored, level


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", "-i", default="-")
    p.add_argument("--current-version", default="0.0.0")
    p.add_argument("--version")
    p.add_argument("--date", default=str(date.today()))
    p.add_argument("--output", "-o", type=Path)
    a = p.parse_args()
    try:
        lines = (
            sys.stdin.readlines()
            if a.input == "-"
            else Path(a.input).read_text(encoding="utf-8").splitlines()
        )
        grouped, breaking, ignored, level = parse(lines)
        version = a.version or bump(a.current_version, level)
        out = [f"## [{version}] - {a.date}", ""]
        if breaking:
            out += ["### Breaking", ""] + [f"- {x}" for x in breaking] + [""]
        for group in ("Added", "Changed", "Fixed"):
            if grouped.get(group):
                out += [f"### {group}", ""] + [f"- {x}" for x in grouped[group]] + [""]
        if not any(grouped.values()):
            out += ["_No Conventional Commit entries found._", ""]
        out += [
            f"<!-- Suggested version bump: {level}; ignored messages: {len(ignored)} -->",
            "",
        ]
        output = "\n".join(out)
        if a.output:
            a.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
