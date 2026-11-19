#!./.venv/bin/python
"""Validate an architecture/specification Markdown document for required sections.

Usage: python spec_validator.py ARCHITECTURE.md [--format text|json]
Exit codes: 0 complete, 1 required sections missing, 2 input/usage error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CRITERIA = [
    (
        "system_context",
        "System context",
        "required",
        [r"system\s+context", r"context\s+diagram"],
    ),
    (
        "component_diagram",
        "Component diagram/architecture",
        "required",
        [r"component\s+(diagram|architecture)", r"architecture\s+diagram"],
    ),
    (
        "api_contracts",
        "API contracts",
        "required",
        [r"api\s+(and\s+)?contracts?", r"interface\s+contracts?"],
    ),
    ("data_model", "Data model", "required", [r"data\s+model", r"data\s+contracts?"]),
    ("tdd_rubric", "TDD rubric", "required", [r"tdd\s+rubric", r"testing\s+strategy"]),
    (
        "threat_model",
        "Security threat model",
        "required",
        [r"security\s+threat\s+model", r"threat\s+model"],
    ),
    (
        "acceptance_criteria",
        "Acceptance criteria",
        "required",
        [r"acceptance\s+criteria", r"given\s*/?\s*when\s*/?\s*then"],
    ),
    (
        "non_functional",
        "Non-functional requirements",
        "recommended",
        [r"non[- ]functional\s+requirements?", r"quality\s+attributes?"],
    ),
    (
        "decision_log",
        "Decision log",
        "recommended",
        [r"decision\s+log", r"architecture\s+decisions?"],
    ),
]


def headings(text):
    return [m.group(1).strip() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.MULTILINE)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec_file", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        text = args.spec_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot read {args.spec_file}: {exc}", file=sys.stderr)
        return 2
    if not text.strip():
        print("error: specification is empty", file=sys.stderr)
        return 2
    corpus = "\n".join(headings(text)).lower()
    results = []
    for key, label, severity, patterns in CRITERIA:
        present = any(re.search(pattern, corpus, re.IGNORECASE) for pattern in patterns)
        results.append(
            {"id": key, "section": label, "severity": severity, "present": present}
        )
    missing = [item for item in results if not item["present"]]
    payload = {
        "file": str(args.spec_file),
        "complete": not any(x["severity"] == "required" for x in missing),
        "checks": results,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"Specification completeness: {'PASS' if payload['complete'] else 'FAIL'}"
        )
        for item in results:
            mark = "PASS" if item["present"] else "MISSING"
            print(f"[{mark:7}] {item['severity'].upper():11} {item['section']}")
        if missing:
            print(
                "\nAdd the missing headings and document observable contracts beneath them."
            )
    return 0 if payload["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
