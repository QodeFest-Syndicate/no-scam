#!./.venv/bin/python
"""Evaluate a product repository for essential go-to-market artifacts.

Usage: ./gtm_readiness_checker.py /path/to/product --max-changelog-age-days 90
Outputs a JSON completeness score and evidence/gaps for each requirement.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

CHECKS = {
    "api_documentation": ["**/openapi*.yaml", "**/openapi*.json", "**/api/**/*.*"],
    "published_sdk": ["**/sdk/**/*.*", "**/pyproject.toml", "**/package.json"],
    "pricing_content": ["**/pricing*.md", "**/pricing/**/*.*"],
    "onboarding_flow": ["**/onboarding*.md", "**/onboarding/**/*.*"],
    "sla_document": ["**/sla*.md", "**/service-level*.md"],
    "compliance_attestation": [
        "**/compliance/**/*.*",
        "**/soc2*.md",
        "**/security-whitepaper*.md",
    ],
    "changelog": ["**/CHANGELOG*", "**/changelog*"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check GTM artifact completeness without modifying the repository."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-changelog-age-days", type=int, default=90)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def candidates(root: Path, patterns: list) -> list:
    found = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and not any(
                part.startswith(".") for part in path.relative_to(root).parts
            ):
                found.add(path)
    return sorted(found)


def substantive(path: Path) -> bool:
    try:
        return path.stat().st_size >= 80 and bool(
            path.read_text(encoding="utf-8", errors="ignore").strip()
        )
    except OSError:
        return False


def check(root: Path, max_age: int) -> dict:
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    results = {}
    for name, patterns in CHECKS.items():
        found = candidates(root, patterns)
        complete = [path for path in found if substantive(path)]
        status = "complete" if complete else "incomplete" if found else "missing"
        detail = {
            "status": status,
            "evidence": [str(path.relative_to(root)) for path in complete[:10]],
        }
        if name == "changelog" and complete:
            newest = max(path.stat().st_mtime for path in complete)
            age = (dt.datetime.now().timestamp() - newest) / 86400
            detail["age_days"] = round(age, 1)
            if age > max_age:
                detail["status"] = "stale"
                detail["gap"] = f"changelog is older than {max_age} days"
        if detail["status"] != "complete" and "gap" not in detail:
            detail["gap"] = f"add substantive {name.replace('_', ' ')} evidence"
        results[name] = detail
    complete_count = sum(item["status"] == "complete" for item in results.values())
    return {
        "root": str(root),
        "score_percent": round(100 * complete_count / len(results), 1),
        "ready": complete_count == len(results),
        "complete": complete_count,
        "required": len(results),
        "checks": results,
    }


def main() -> int:
    args = parse_args()
    if args.max_changelog_age_days < 1:
        print("error: age must be at least one day", file=sys.stderr)
        return 2
    try:
        report = check(args.root.resolve(), args.max_changelog_age_days)
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0 if report["ready"] else 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
