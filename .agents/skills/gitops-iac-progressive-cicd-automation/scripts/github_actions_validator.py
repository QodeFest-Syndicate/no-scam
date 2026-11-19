#!./.venv/bin/python
"""Validate GitHub Actions workflows for reproducibility and security hygiene.

Usage: python github_actions_validator.py .github/workflows [--format text|json]
Branch-protection required checks must also be verified through repository settings.
"""

import argparse
import json
import re
import sys
from pathlib import Path

USES = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
DEPRECATED = {
    "actions/checkout@v1",
    "actions/checkout@v2",
    "actions/setup-node@v1",
    "actions/cache@v1",
    "actions/upload-artifact@v1",
    "actions/download-artifact@v1",
}
SHA = re.compile(r"^[^@]+@[0-9a-fA-F]{40}$")


def validate(path, text):
    findings = []

    def add(severity, line, message):
        findings.append(
            {"severity": severity, "file": str(path), "line": line, "message": message}
        )

    for match in USES.finditer(text):
        action = match.group(1)
        line = text.count("\n", 0, match.start()) + 1
        if action.startswith("./") or action.startswith("docker://"):
            continue
        if action in DEPRECATED:
            add("high", line, f"deprecated action version: {action}")
        if not SHA.match(action):
            add(
                "high" if action.endswith(("@main", "@master")) else "medium",
                line,
                f"action is not pinned to an immutable 40-character SHA: {action}",
            )
    for n, line in enumerate(text.splitlines(), 1):
        if (
            re.search(
                r"(?i)\b(password|token|api[_-]?key|secret)\s*:\s*(?!\$\{\{\s*secrets\.)[^#\s][^#]*$",
                line,
            )
            and "permissions:" not in line
        ):
            add(
                "critical",
                n,
                "possible literal secret; use ${{ secrets.NAME }} or OIDC",
            )
    if not re.search(r"(?m)^\s*permissions\s*:", text):
        add("high", 1, "workflow has no explicit least-privilege permissions block")
    if not re.search(r"(?m)^\s*timeout-minutes\s*:\s*\d+", text):
        add("medium", 1, "no timeout-minutes found for any job")
    if not re.search(r"(?m)^\s*pull_request\s*:", text):
        add(
            "medium",
            1,
            "workflow does not expose pull_request checks; verify required status-check coverage",
        )
    if re.search(r"(?m)^\s*pull_request_target\s*:", text) and re.search(
        r"(?m)^\s*uses:\s*actions/checkout", text
    ):
        add(
            "critical",
            1,
            "pull_request_target with checkout needs explicit untrusted-code review",
        )
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=Path)
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    if not a.path.exists():
        p.error("path does not exist")
    files = (
        [a.path]
        if a.path.is_file()
        else sorted(set(a.path.rglob("*.yml")) | set(a.path.rglob("*.yaml")))
    )
    findings = []
    for path in files:
        try:
            findings.extend(validate(path, path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError) as exc:
            print(f"warning: {path}: {exc}", file=sys.stderr)
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (rank[f["severity"]], f["file"], f["line"]))
    if a.format == "json":
        print(
            json.dumps(
                {
                    "findings": findings,
                    "note": "Verify branch-protection required checks separately.",
                },
                indent=2,
            )
        )
    elif findings:
        for f in findings:
            print(f"[{f['severity'].upper()}] {f['file']}:{f['line']} {f['message']}")
    else:
        print(
            "PASS: no workflow hygiene findings; verify branch protection separately."
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
