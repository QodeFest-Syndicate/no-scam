#!./.venv/bin/python
"""Validate developer-portal content structure and minimum completeness.

Usage: ./developer_portal_validator.py ./portal --min-words 40
Checks getting started, auth, API reference, SDKs, examples, changelog, and status link.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SECTIONS = {
    "getting_started": ["**/getting-started*", "**/quickstart*"],
    "authentication": ["**/authentication*", "**/auth*"],
    "api_reference": ["**/api-reference/**/*", "**/reference/**/*", "**/openapi*"],
    "sdk_quickstarts": ["**/sdk*/**/*", "**/*sdk*quickstart*"],
    "code_examples": ["**/examples/**/*", "**/code-examples/**/*"],
    "changelog": ["**/CHANGELOG*", "**/changelog*"],
}
STATUS_RE = re.compile(r"https?://[^\s)\]>]*status[^\s)\]>]*", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|lorem ipsum|coming soon)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report missing or incomplete developer portal sections."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--min-words", type=int, default=40)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def find(root: Path, patterns: list) -> list:
    result = set()
    for pattern in patterns:
        result.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(result)


def inspect(path: Path, min_words: int) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    word_count = len(re.findall(r"\b[\w'-]+\b", text))
    placeholders = sorted(
        set(match.group(0).upper() for match in PLACEHOLDER_RE.finditer(text))
    )
    return {
        "path": str(path),
        "word_count": word_count,
        "placeholders": placeholders,
        "complete": word_count >= min_words and not placeholders,
    }


def validate(root: Path, min_words: int) -> dict:
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    results = {}
    all_text = []
    for name, patterns in SECTIONS.items():
        paths = find(root, patterns)
        evidence = [inspect(path, min_words) for path in paths]
        for item in evidence:
            item["path"] = str(Path(item["path"]).relative_to(root))
        complete = any(item["complete"] for item in evidence)
        results[name] = {
            "status": "complete" if complete else "incomplete" if paths else "missing",
            "evidence": evidence[:10],
        }
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {
            ".md",
            ".mdx",
            ".html",
            ".json",
            ".yaml",
            ".yml",
        }:
            try:
                all_text.append(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    status_urls = sorted(set(STATUS_RE.findall("\n".join(all_text))))
    results["status_page"] = {
        "status": "complete" if status_urls else "missing",
        "urls": status_urls,
    }
    complete = sum(item["status"] == "complete" for item in results.values())
    return {
        "root": str(root),
        "complete": complete,
        "required": len(results),
        "score_percent": round(100 * complete / len(results), 1),
        "valid": complete == len(results),
        "sections": results,
    }


def main() -> int:
    args = parse_args()
    if args.min_words < 1:
        print("error: --min-words must be positive", file=sys.stderr)
        return 2
    try:
        report = validate(args.root.resolve(), args.min_words)
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0 if report["valid"] else 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
