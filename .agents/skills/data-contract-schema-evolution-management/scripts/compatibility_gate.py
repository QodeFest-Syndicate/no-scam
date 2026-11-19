#!./.venv/bin/python
"""CI gate for schema compatibility strategies.

Usage:
  compatibility_gate.py current.json proposed.json --strategy BACKWARD

Strategies: BACKWARD (new readers consume old data), FORWARD (old readers
consume new data), FULL (both), or NONE (report only). Exits 0 on pass and 1 on
compatibility failure; malformed input exits 2.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_fields(path: Path) -> dict[str, dict[str, Any]]:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    if not isinstance(schema, dict):
        raise ValueError(f"{path} must contain an object")
    result: dict[str, dict[str, Any]] = {}
    if isinstance(schema.get("properties"), dict):
        required = set(schema.get("required", []))
        entries = [
            (name, spec if isinstance(spec, dict) else {"type": spec})
            for name, spec in schema["properties"].items()
        ]
        for name, spec in entries:
            raw_type = spec.get("type", "any")
            result[name] = {
                "type": canonical_type(raw_type),
                "required": name in required,
                "nullable": has_null(raw_type),
                "default": "default" in spec,
            }
    elif isinstance(schema.get("fields"), list):
        avro = schema.get("type") == "record"
        for field in schema["fields"]:
            if not isinstance(field, dict) or "name" not in field:
                raise ValueError(f"invalid field in {path}")
            raw_type = field.get("type", "unknown")
            optional = (
                (has_null(raw_type) or "default" in field)
                if avro
                else bool(
                    field.get("optional")
                    or str(field.get("label", "")).lower() in ("optional", "repeated")
                )
            )
            result[str(field["name"])] = {
                "type": canonical_type(raw_type),
                "required": not optional,
                "nullable": has_null(raw_type),
                "default": "default" in field,
            }
    else:
        raise ValueError(f"unsupported schema shape in {path}")
    return result


def canonical_type(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(sorted(canonical_type(item) for item in value))
    if isinstance(value, dict):
        return canonical_type(value.get("type", value.get("name", "object")))
    return str(value)


def has_null(value: Any) -> bool:
    return (
        "null" in value
        if isinstance(value, list)
        else isinstance(value, dict) and has_null(value.get("type")) or value == "null"
    )


def assess(
    old: dict[str, dict[str, Any]], new: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    backward: list[dict[str, Any]] = []
    forward: list[dict[str, Any]] = []

    def issue(target: list[dict[str, Any]], field: str, reason: str) -> None:
        target.append({"field": field, "reason": reason})

    for name in sorted(set(new) - set(old)):
        if new[name]["required"] and not new[name]["default"]:
            issue(backward, name, "new required field has no default for old records")
    for name in sorted(set(old) - set(new)):
        if old[name]["required"]:
            issue(forward, name, "field required by old readers was removed")
    for name in sorted(set(old) & set(new)):
        before, after = old[name], new[name]
        if before["type"] != after["type"]:
            issue(
                backward, name, f"type changed from {before['type']} to {after['type']}"
            )
            issue(
                forward, name, f"type changed from {before['type']} to {after['type']}"
            )
        if not before["required"] and after["required"] and not after["default"]:
            issue(backward, name, "optional field became required without a default")
        if before["nullable"] and not after["nullable"]:
            issue(backward, name, "nullable field became non-nullable")
        if not before["nullable"] and after["nullable"]:
            issue(forward, name, "new data may contain null unsupported by old readers")
    return backward, forward


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("current", type=Path, help="current schema JSON")
    parser.add_argument("proposed", type=Path, help="proposed schema JSON")
    parser.add_argument(
        "--strategy",
        choices=("BACKWARD", "FORWARD", "FULL", "NONE"),
        default="BACKWARD",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        backward, forward = assess(
            load_fields(args.current), load_fields(args.proposed)
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    relevant = {
        "BACKWARD": backward,
        "FORWARD": forward,
        "FULL": backward + forward,
        "NONE": [],
    }[args.strategy]
    passed = not relevant
    report = {
        "strategy": args.strategy,
        "passed": passed,
        "backward_issues": backward,
        "forward_issues": forward,
        "decision": "PASS" if passed else "FAIL",
    }
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"Compatibility gate: {report['decision']} ({args.strategy})")
        for direction, issues in (("BACKWARD", backward), ("FORWARD", forward)):
            for item in issues:
                marker = "BLOCK" if args.strategy in (direction, "FULL") else "INFO"
                print(f"- [{marker}] {direction} {item['field']}: {item['reason']}")
        if not backward and not forward:
            print("- no compatibility issues detected")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
