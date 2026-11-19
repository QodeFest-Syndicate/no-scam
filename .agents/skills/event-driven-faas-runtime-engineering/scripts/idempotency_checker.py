#!./.venv/bin/python
"""Statically flag common idempotency risks in FaaS handler source.

Usage: idempotency_checker.py handler.py [--format text|json] [--strict]

This heuristic scanner supports Python, JavaScript/TypeScript, and Go. Findings
must be reviewed in context; absence of findings is not proof of idempotency.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

RULES = [
    {
        "id": "random-id-side-effect",
        "severity": "high",
        "pattern": r"(?:uuid\.uuid4|randomUUID|Math\.random|crypto/rand|rand\.(?:Int|Read))",
        "message": "Random identifier may change on replay; derive identity from the idempotency key.",
    },
    {
        "id": "append-only-write",
        "severity": "high",
        "pattern": r"(?:\.append\s*\(|INSERT\s+INTO|PutObject|\.create\s*\(|Add\s*\()",
        "message": "Append/create side effect needs an upsert, conditional write, or duplicate guard.",
    },
    {
        "id": "mutable-global",
        "severity": "medium",
        "pattern": r"(?m)^(?:[A-Za-z_]\w*\s*=\s*(?:\[|\{|set\(|dict\(|list\()|(?:let|var)\s+\w+\s*=|var\s+\w+\s+(?:map|\[))",
        "message": "Module-level mutable state can leak across warm invocations.",
    },
    {
        "id": "non-conditional-http-mutation",
        "severity": "medium",
        "pattern": r"(?:requests\.(?:post|patch)|fetch\s*\([^\n]+method\s*:\s*['\"]POST|http\.Post\s*\()",
        "message": "Outbound mutation should forward an idempotency token or use a conditional contract.",
    },
]
DEDUP_PATTERNS = (
    r"idempoten(?:cy|t)",
    r"dedup",
    r"messageI[dD]",
    r"event[_-]?[iI][dD]",
    r"conditional",
    r"if[_-]?none[_-]?match",
    r"upsert",
    r"ON\s+CONFLICT",
    r"attribute_not_exists",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("source", type=Path, help="Handler source file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any high-severity risk exists",
    )
    return parser.parse_args()


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def scan(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    findings = []
    has_dedup = any(
        re.search(pattern, text, re.IGNORECASE) for pattern in DEDUP_PATTERNS
    )
    if not has_dedup:
        findings.append(
            {
                "rule": "missing-deduplication-check",
                "severity": "critical",
                "line": 1,
                "message": "No stable event/idempotency key or deduplication guard was detected.",
            }
        )
    for rule in RULES:
        for match in re.finditer(rule["pattern"], text, re.IGNORECASE):
            findings.append(
                {
                    "rule": rule["id"],
                    "severity": rule["severity"],
                    "line": line_number(text, match.start()),
                    "message": rule["message"],
                    "evidence": match.group(0)[:120],
                }
            )
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda item: (order[item["severity"]], item["line"]))
    return {
        "source": str(path),
        "deduplication_signal_detected": has_dedup,
        "risk_count": len(findings),
        "findings": findings,
        "limitations": "Heuristic scan; verify transaction boundaries, downstream contracts, and ledger atomicity manually.",
    }


def render_text(report: dict[str, Any]) -> None:
    print(f"Idempotency audit: {report['source']}")
    print(
        f"Deduplication signal: {'yes' if report['deduplication_signal_detected'] else 'no'}"
    )
    if not report["findings"]:
        print("No common static risks detected.")
    for finding in report["findings"]:
        print(
            f"{finding['severity'].upper():8} line {finding['line']:>4} {finding['rule']}: {finding['message']}"
        )
    print(f"Note: {report['limitations']}")


def main() -> int:
    args = parse_args()
    try:
        report = scan(args.source)
        if args.format == "json":
            json.dump(report, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        else:
            render_text(report)
        severe = any(f["severity"] in {"critical", "high"} for f in report["findings"])
        return 1 if args.strict and severe else 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
