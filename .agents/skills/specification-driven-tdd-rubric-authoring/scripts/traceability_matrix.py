#!./.venv/bin/python
"""Build a requirement-to-test traceability matrix.

Usage: python traceability_matrix.py --spec-file SPEC.md --test-dir tests [--format markdown|json]
Requirements are headings/lines containing IDs such as FR-001, SEC-2, or NFR-LAT-01.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ID_PATTERN = re.compile(
    r"\b(?:FR|NFR(?:-[A-Z]+)?|SEC|DATA|REQ|AC)-\d+(?:-\d+)?\b", re.IGNORECASE
)
TEST_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".java",
    ".rb",
    ".rs",
    ".cs",
    ".feature",
}


def requirements(text):
    found = {}
    for line in text.splitlines():
        ids = ID_PATTERN.findall(line)
        for rid in ids:
            found.setdefault(rid.upper(), re.sub(r"^\s*#+\s*", "", line).strip())
    return found


def scan_tests(root):
    refs = {}
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEST_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        ids = sorted(set(x.upper() for x in ID_PATTERN.findall(text)))
        files.append({"path": str(path), "references": ids})
        for rid in ids:
            refs.setdefault(rid, []).append(str(path))
    return refs, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-file", required=True, type=Path)
    parser.add_argument("--test-dir", required=True, type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    try:
        spec_text = args.spec_file.read_text(encoding="utf-8")
        if not args.test_dir.is_dir():
            raise OSError(f"not a directory: {args.test_dir}")
    except (OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    reqs = requirements(spec_text)
    if not reqs:
        print("error: no stable requirement IDs found in spec", file=sys.stderr)
        return 2
    refs, test_files = scan_tests(args.test_dir)
    rows = [
        {
            "requirement": rid,
            "description": desc,
            "tests": refs.get(rid, []),
            "covered": bool(refs.get(rid)),
        }
        for rid, desc in sorted(reqs.items())
    ]
    orphan_tests = [
        {
            "file": item["path"],
            "references": [rid for rid in item["references"] if rid not in reqs],
        }
        for item in test_files
        if not item["references"] or any(rid not in reqs for rid in item["references"])
    ]
    payload = {
        "matrix": rows,
        "specs_without_tests": [r["requirement"] for r in rows if not r["covered"]],
        "tests_without_spec_references": orphan_tests,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print("| Requirement | Description | Tests | Status |")
        print("|---|---|---|---|")
        for row in rows:
            tests = "<br>".join(row["tests"]) or "—"
            print(
                f"| {row['requirement']} | {row['description'].replace('|', '/')} | {tests} | {'Covered' if row['covered'] else 'GAP'} |"
            )
        print(
            f"\nCoverage gaps: {len(payload['specs_without_tests'])}; orphan/unreferenced test files: {len(orphan_tests)}"
        )
    return 1 if payload["specs_without_tests"] or orphan_tests else 0


if __name__ == "__main__":
    sys.exit(main())
