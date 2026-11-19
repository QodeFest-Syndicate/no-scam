#!./.venv/bin/python
"""Scan a directory for likely hardcoded secrets without printing secret values.

Usage: python secret_scanner.py PATH [--format text|json] [--max-bytes 2000000]
Use findings for triage; rotate confirmed exposed credentials immediately.
"""

import argparse
import json
import re
import sys
from pathlib import Path

PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github-token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9_]{30,255}|github_pat_[A-Za-z0-9_]{20,255})\b"
    ),
    "jwt": re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b"
    ),
    "connection-string": re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:@]+:[^\s@]+@", re.IGNORECASE
    ),
    "assigned-secret": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"]?[^\s'\"${}]{8,}"
    ),
    "base64-credential": re.compile(
        r"(?i)\b(?:authorization|credential|secret)\b\s*[:=]\s*['\"]?[A-Za-z0-9+/]{24,}={0,2}"
    ),
}
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "dist", "build"}
TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".java",
    ".rb",
    ".rs",
    ".cs",
    ".php",
    ".sh",
    ".env",
    ".ini",
    ".conf",
    ".cfg",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".properties",
    ".tf",
    ".hcl",
    ".md",
    ".txt",
}


def scan(root, max_bytes):
    findings = []
    paths = [root] if root.is_file() else root.rglob("*")
    for path in paths:
        if (
            not path.is_file()
            or any(part in SKIP_DIRS for part in path.parts)
            or (
                path.suffix.lower() not in TEXT_SUFFIXES
                and not path.name.startswith(".env")
            )
        ):
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if "pragma: allowlist secret" in line.lower():
                    continue
                for kind, pattern in PATTERNS.items():
                    if pattern.search(line):
                        findings.append(
                            {
                                "file": str(path),
                                "line": number,
                                "type": kind,
                                "severity": "critical"
                                if kind
                                in {"private-key", "aws-access-key", "github-token"}
                                else "high",
                                "preview": "[REDACTED]",
                            }
                        )
        except OSError as exc:
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=Path)
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--max-bytes", type=int, default=2_000_000)
    a = p.parse_args()
    if not a.path.exists() or a.max_bytes <= 0:
        p.error("path must exist and max-bytes must be positive")
    findings = scan(a.path, a.max_bytes)
    if a.format == "json":
        print(json.dumps({"root": str(a.path), "findings": findings}, indent=2))
    elif findings:
        for f in findings:
            print(
                f"[{f['severity'].upper()}] {f['file']}:{f['line']} {f['type']} {f['preview']}"
            )
    else:
        print("PASS: no likely hardcoded secrets detected.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
