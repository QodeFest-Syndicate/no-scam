#!./.venv/bin/python
"""Heuristically audit React components for common accessibility issues.

Usage: component_audit.py PROJECT_DIR [--format text|json] [--strict]

Checks JSX/TSX for images without alt text, unlabeled icon buttons/inputs,
non-native onClick handlers without keyboard support, and hard-coded color
pairs that require contrast review. Confirm findings with an accessibility tree.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

EXTENSIONS = {".jsx", ".tsx", ".js", ".ts"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("project", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 when high-severity findings exist"
    )
    return parser.parse_args()


def line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def add(
    findings: list[dict[str, Any]],
    path: Path,
    text: str,
    offset: int,
    rule: str,
    severity: str,
    message: str,
) -> None:
    findings.append(
        {
            "file": str(path),
            "line": line(text, offset),
            "rule": rule,
            "severity": severity,
            "message": message,
        }
    )


def audit_file(path: Path, findings: list[dict[str, Any]]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        findings.append(
            {
                "file": str(path),
                "line": 1,
                "rule": "unreadable",
                "severity": "medium",
                "message": str(exc),
            }
        )
        return
    for match in re.finditer(r"<img\b([^>]*)>", text, re.IGNORECASE | re.DOTALL):
        attrs = match.group(1)
        if not re.search(r"\balt\s*=", attrs):
            add(
                findings,
                path,
                text,
                match.start(),
                "image-alt",
                "high",
                'Image has no alt attribute; use alt="" for decorative images.',
            )
    for match in re.finditer(
        r"<(?:input|select|textarea)\b([^>]*)>", text, re.IGNORECASE | re.DOTALL
    ):
        attrs = match.group(1)
        if not re.search(r"\b(?:aria-label|aria-labelledby|id)\s*=", attrs):
            add(
                findings,
                path,
                text,
                match.start(),
                "form-label",
                "high",
                "Form control has no detectable label association.",
            )
    for match in re.finditer(
        r"<button\b([^>]*)>([\s\S]*?)</button>", text, re.IGNORECASE
    ):
        attrs, children = match.groups()
        plain = re.sub(r"<[^>]+>|\{[^}]*\}", "", children).strip()
        if not plain and not re.search(r"\b(?:aria-label|aria-labelledby)\s*=", attrs):
            add(
                findings,
                path,
                text,
                match.start(),
                "button-name",
                "high",
                "Button appears to have no accessible name.",
            )
    for match in re.finditer(
        r"<([A-Za-z][\w.]*)\b([^>]*)\bonClick\s*=([^>]*)>", text, re.DOTALL
    ):
        tag, before, after = match.groups()
        if tag.lower() not in {"button", "a", "input", "select", "textarea"}:
            attrs = before + after
            if not re.search(r"\bonKey(?:Down|Up|Press)\s*=", attrs):
                add(
                    findings,
                    path,
                    text,
                    match.start(),
                    "click-keyboard",
                    "high",
                    f"<{tag}> has onClick without a keyboard handler; prefer a semantic button/link.",
                )
            if not re.search(r"\b(?:role|tabIndex)\s*=", attrs):
                add(
                    findings,
                    path,
                    text,
                    match.start(),
                    "interactive-semantics",
                    "medium",
                    f"<{tag}> may not be focusable or expose an interactive role.",
                )
    for match in re.finditer(
        r"(?:color|background(?:Color)?)[\s:'\"]+#[0-9a-fA-F]{3,8}", text
    ):
        add(
            findings,
            path,
            text,
            match.start(),
            "contrast-review",
            "low",
            "Hard-coded color detected; verify 4.5:1 text or 3:1 large-text/UI contrast.",
        )


def main() -> int:
    args = parse_args()
    try:
        if not args.project.is_dir():
            raise ValueError(f"not a directory: {args.project}")
        ignored = {"node_modules", "dist", "build", ".next", "coverage", ".git"}
        files = [
            p
            for p in args.project.rglob("*")
            if p.suffix.lower() in EXTENSIONS and not ignored.intersection(p.parts)
        ]
        findings: list[dict[str, Any]] = []
        for path in sorted(files):
            audit_file(path, findings)
        report = {
            "project": str(args.project),
            "files_scanned": len(files),
            "finding_count": len(findings),
            "findings": findings,
        }
        if args.format == "json":
            json.dump(report, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        else:
            print(f"Component audit: {len(files)} files, {len(findings)} findings")
            for item in findings:
                print(
                    f"{item['severity'].upper():6} {item['file']}:{item['line']} {item['rule']}: {item['message']}"
                )
        return (
            1 if args.strict and any(f["severity"] == "high" for f in findings) else 0
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
