#!./.venv/bin/python
"""Generate a TDD rubric from YAML requirements.

Usage: python rubric_generator.py requirements.yaml --output rubric.md --format markdown
Input may be a list or contain a top-level `requirements` list. PyYAML is required.
"""

import argparse
import sys
from pathlib import Path


def load_yaml(path):
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required: install with `python -m pip install pyyaml`"
        ) from exc
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise RuntimeError(f"cannot parse {path}: {exc}") from exc
    reqs = data.get("requirements", []) if isinstance(data, dict) else data
    if not isinstance(reqs, list) or not reqs:
        raise RuntimeError("input must contain a non-empty requirements list")
    return reqs, yaml


def normalize(item, index):
    if isinstance(item, str):
        return {
            "id": f"REQ-{index:03d}",
            "title": item,
            "description": item,
            "threshold": "All mandatory scenarios pass",
            "test_data": "Define valid, invalid, boundary, and privacy-safe fixtures",
        }
    if not isinstance(item, dict):
        raise RuntimeError(f"requirement {index} must be a string or mapping")
    rid = str(item.get("id") or f"REQ-{index:03d}")
    title = str(item.get("title") or item.get("name") or item.get("description") or rid)
    return {
        "id": rid,
        "title": title,
        "description": str(item.get("description") or title),
        "threshold": item.get("acceptance_threshold", "All mandatory scenarios pass"),
        "test_data": item.get(
            "test_data", "Define valid, invalid, boundary, and privacy-safe fixtures"
        ),
    }


def markdown(requirements):
    lines = [
        "# TDD Rubric",
        "",
        "> Complete each scenario before implementation; retain failing and passing evidence.",
        "",
    ]
    for req in requirements:
        lines += [
            f"## {req['id']} — {req['title']}",
            "",
            req["description"],
            "",
            "### Scenario",
            "",
            f"- **Given:** [precondition, actor, and state for {req['id']}]",
            "- **When:** [single observable action or event]",
            "- **Then:** [measurable result and side effects]",
            "- **And:** [negative, boundary, or recovery invariant]",
            "",
            f"**Acceptance threshold:** {req['threshold']}",
            "",
            f"**Test-data requirements:** {req['test_data']}",
            "",
            "**Evidence:** [test ID, layer, command, report path]",
            "",
        ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--format", choices=("markdown", "yaml"), default="markdown")
    args = parser.parse_args()
    try:
        raw, yaml = load_yaml(args.requirements)
        requirements = [normalize(item, i) for i, item in enumerate(raw, 1)]
        output = (
            markdown(requirements)
            if args.format == "markdown"
            else yaml.safe_dump({"tdd_rubric": requirements}, sort_keys=False)
        )
        if args.output:
            args.output.write_text(
                output + ("" if output.endswith("\n") else "\n"), encoding="utf-8"
            )
        else:
            print(output)
    except (RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
