#!./.venv/bin/python
"""Regex-based Terraform/HCL linter for common safety and hygiene issues.

Usage: python iac_linter.py PATH [--format text|json]
Exit code 1 indicates findings. Confirm findings with Terraform validation/policy tools.
"""

import argparse
import json
import re
import sys
from pathlib import Path

RESOURCE = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', re.MULTILINE)
CRITICAL = re.compile(
    r"aws_(?:db_instance|rds_cluster|s3_bucket|dynamodb_table|efs_file_system)|google_sql_database_instance|azurerm_(?:storage_account|mssql_server)"
)


def blocks(text):
    for match in RESOURCE.finditer(text):
        depth = 0
        end = len(text)
        for pos in range(match.end() - 1, len(text)):
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break
        yield match.group(1), match.group(2), match.start(), text[match.start() : end]


def lint(path, text):
    findings = []
    for n, line in enumerate(text.splitlines(), 1):
        if re.search(
            r"(?i)\b(password|secret|api[_-]?key|token)\b\s*=\s*\"(?!\$\{|var\.|data\.)[^\"]+\"",
            line,
        ):
            findings.append(("critical", n, "Possible hardcoded secret"))
        if re.search(r"cidr_blocks\s*=\s*\[[^\]]*\"0\.0\.0\.0/0\"", line):
            findings.append(
                (
                    "critical",
                    n,
                    "Security rule permits 0.0.0.0/0; verify port and necessity",
                )
            )
        if re.search(r"ipv6_cidr_blocks\s*=\s*\[[^\]]*\"::/0\"", line):
            findings.append(("critical", n, "Security rule permits ::/0"))
    for rtype, name, offset, block in blocks(text):
        line = text.count("\n", 0, offset) + 1
        if not re.search(r"\b(tags|labels)\s*=", block):
            findings.append(("medium", line, f"{rtype}.{name} has no tags/labels"))
        if CRITICAL.search(rtype) and not re.search(
            r"lifecycle\s*\{[\s\S]*?prevent_destroy\s*=\s*true", block
        ):
            findings.append(
                (
                    "high",
                    line,
                    f"critical resource {rtype}.{name} lacks lifecycle prevent_destroy",
                )
            )
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return [
        {"severity": s, "file": str(path), "line": n, "message": m}
        for s, n, m in sorted(findings, key=lambda x: (rank[x[0]], x[1]))
    ]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=Path)
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    if not a.path.exists():
        p.error("path does not exist")
    files = [a.path] if a.path.is_file() else list(a.path.rglob("*.tf"))
    findings = []
    texts = {}
    for path in files:
        try:
            texts[path] = path.read_text(encoding="utf-8")
            findings.extend(lint(path, texts[path]))
        except (OSError, UnicodeError) as exc:
            print(f"warning: {path}: {exc}", file=sys.stderr)
    if texts and not any(
        re.search(r"terraform\s*\{[\s\S]*?backend\s+\"", text)
        for text in texts.values()
    ):
        findings.append(
            {
                "severity": "high",
                "file": str(a.path),
                "line": 1,
                "message": "No remote/backend state configuration detected in the scanned scope",
            }
        )
    if a.format == "json":
        print(json.dumps({"findings": findings}, indent=2))
    elif findings:
        for f in findings:
            print(f"[{f['severity'].upper()}] {f['file']}:{f['line']} {f['message']}")
    else:
        print("PASS: no heuristic IaC findings.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
