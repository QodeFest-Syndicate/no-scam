#!./.venv/bin/python
"""Scan source/config files for fields and values that may handle regulated data.

Usage: python data_classification_scanner.py PATH [--format text|json]
Findings identify review locations; output does not reproduce detected values.
"""

import argparse
import json
import re
import sys
from pathlib import Path

RULES = [
    (
        "PII",
        "email",
        re.compile(
            r"\b(?:e[-_]?mail|email_address)\b|\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "PII",
        "phone",
        re.compile(
            r"\b(?:phone|mobile|telephone)(?:[_-]?(?:number|no))?\b|\+?\d[\d ().-]{7,}\d",
            re.IGNORECASE,
        ),
    ),
    (
        "PII",
        "government-id",
        re.compile(
            r"\b(?:ssn|social[_ -]?security|national[_ -]?id|passport[_ -]?(?:number|no))\b|\b\d{3}-\d{2}-\d{4}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "PII",
        "person-name",
        re.compile(r"\b(?:first|last|full|given|family)[_-]?name\b", re.IGNORECASE),
    ),
    (
        "Payment",
        "card-number",
        re.compile(
            r"\b(?:card[_ -]?(?:number|no)|pan)\b|\b(?:\d[ -]*?){13,19}\b", re.IGNORECASE
        ),
    ),
    ("Payment", "cvv", re.compile(r"\b(?:cvv|cvc|card[_ -]?verification)\b", re.IGNORECASE)),
]
SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".java",
    ".rb",
    ".cs",
    ".php",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".ini",
    ".tf",
    ".hcl",
    ".env",
}


def controls(line):
    present = []
    if re.search(r"encrypt|cipher|kms|vault|tokeni[sz]", line, re.IGNORECASE):
        present.append("encryption/tokenization")
    if re.search(r"mask|redact|hash|pseudonym", line, re.IGNORECASE):
        present.append("masking")
    return present


def scan(root):
    findings = []
    paths = [root] if root.is_file() else root.rglob("*")
    for path in paths:
        if (
            not path.is_file()
            or (
                path.suffix.lower() not in SUFFIXES and not path.name.startswith(".env")
            )
            or any(x in path.parts for x in (".git", "node_modules", ".venv"))
        ):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            print(f"warning: {path}: {exc}", file=sys.stderr)
            continue
        for number, line in enumerate(lines, 1):
            for classification, kind, pattern in RULES:
                if pattern.search(line):
                    found_controls = controls(line)
                    findings.append(
                        {
                            "file": str(path),
                            "line": number,
                            "classification": classification,
                            "type": kind,
                            "controls_seen": found_controls,
                            "recommendation": "verify purpose, access, masking, encryption, retention, and non-production handling"
                            if not found_controls
                            else "verify control effectiveness and key/token scope",
                        }
                    )
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=Path)
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    if not a.path.exists():
        p.error("path does not exist")
    findings = scan(a.path)
    if a.format == "json":
        print(json.dumps({"root": str(a.path), "findings": findings}, indent=2))
    elif findings:
        for f in findings:
            print(
                f"[{f['classification']}] {f['file']}:{f['line']} {f['type']}: {f['recommendation']}"
            )
    else:
        print("No regulated-data patterns detected.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
