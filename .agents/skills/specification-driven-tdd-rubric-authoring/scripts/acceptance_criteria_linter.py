#!./.venv/bin/python
"""Lint Markdown acceptance criteria for testability and suggest rewrites.

Usage: python acceptance_criteria_linter.py criteria.md [--format text|json]
Returns 1 when actionable findings are present.
"""

import argparse
import json
import re
import sys
from pathlib import Path

VAGUE = {
    "fast": "state a latency percentile, threshold, load, and measurement window",
    "user-friendly": "name the user task and measurable completion/error target",
    "secure": "name the threat, control, authorization rule, and verification test",
    "robust": "define failure modes, retry limits, and recovery outcome",
    "scalable": "define workload, growth range, resource ceiling, and SLO",
    "soon": "state an elapsed-time limit with units",
    "appropriate": "state the governing rule or numeric range",
}
ACTOR = re.compile(r"\b(user|admin|operator|system|service|they|someone)\b", re.IGNORECASE)
BOUNDARY = re.compile(
    r"\b(empty|zero|minimum|maximum|invalid|missing|duplicate|timeout|unauthori[sz]ed|boundary|limit|less than|greater than)\b",
    re.IGNORECASE,
)
QUALITATIVE = re.compile(
    r"\b(easy|simple|intuitive|seamless|good|best|high quality|reliable)\b", re.IGNORECASE
)


def candidates(text):
    blocks = re.split(r"(?=^#{2,6}\s+|^\s*(?:[-*]|\d+\.)\s+)", text, flags=re.MULTILINE)
    return [
        (i, b.strip())
        for i, b in enumerate(blocks, 1)
        if b.strip() and not b.lstrip().startswith("# ")
    ]


def lint(text):
    findings = []
    for index, block in candidates(text):
        lower = block.lower()
        for term, rewrite in VAGUE.items():
            if re.search(rf"\b{re.escape(term)}\b", lower):
                findings.append(
                    {
                        "criterion": index,
                        "rule": "vague-term",
                        "term": term,
                        "message": f"Replace '{term}': {rewrite}.",
                    }
                )
        if not ACTOR.search(block) and (
            "when" in lower or "shall" in lower or "must" in lower
        ):
            findings.append(
                {
                    "criterion": index,
                    "rule": "ambiguous-actor",
                    "message": "Name a specific authenticated actor or originating system.",
                }
            )
        if QUALITATIVE.search(block) and not re.search(
            r"\d|%|milliseconds?|seconds?|minutes?", block, re.IGNORECASE
        ):
            findings.append(
                {
                    "criterion": index,
                    "rule": "untestable-assertion",
                    "message": "Replace qualitative judgment with an observable metric and threshold.",
                }
            )
        if (
            "given" in lower or "when" in lower or "then" in lower
        ) and not BOUNDARY.search(block):
            findings.append(
                {
                    "criterion": index,
                    "rule": "missing-boundary",
                    "message": "Add at least one invalid, empty, limit, duplicate, timeout, or unauthorized scenario.",
                }
            )
        if "then" in lower and not re.search(
            r"\bthen\b.+(?:\d|must|returns?|emits?|stores?|rejects?|does not)",
            block,
            re.IGNORECASE | re.DOTALL,
        ):
            findings.append(
                {
                    "criterion": index,
                    "rule": "weak-outcome",
                    "message": "Rewrite Then as a directly observable result with an exact pass/fail threshold.",
                }
            )
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("criteria_file", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        text = args.criteria_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot read input: {exc}", file=sys.stderr)
        return 2
    findings = lint(text)
    if args.format == "json":
        print(
            json.dumps(
                {"file": str(args.criteria_file), "findings": findings}, indent=2
            )
        )
    elif findings:
        for item in findings:
            print(f"criterion {item['criterion']} [{item['rule']}]: {item['message']}")
        print(f"\n{len(findings)} actionable finding(s).")
    else:
        print("PASS: no testability issues detected.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
