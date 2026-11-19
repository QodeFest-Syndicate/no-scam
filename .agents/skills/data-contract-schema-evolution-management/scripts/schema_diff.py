#!./.venv/bin/python
"""Produce a compatibility-classified diff between two JSON schema versions.

Usage:
  schema_diff.py current.json proposed.json [--format text|json]

Supports JSON Schema ``properties`` and Avro/Protobuf-JSON ``fields`` lists.
The report covers additions, removals, types, defaults, and nullability.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MISSING = object()


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"schema {path} must be an object")
    return value


def type_label(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(sorted(type_label(item) for item in value))
    if isinstance(value, dict):
        return str(
            value.get("type") or value.get("name") or json.dumps(value, sort_keys=True)
        )
    return str(value)


def nullable(value: Any) -> bool:
    if isinstance(value, list):
        return "null" in value
    if isinstance(value, dict):
        return nullable(value.get("type")) or bool(value.get("nullable"))
    return value == "null"


def normalize(schema: dict[str, Any]) -> tuple[str, dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, Any]] = {}
    if isinstance(schema.get("properties"), dict):
        fmt = "json-schema"
        required = set(schema.get("required", []))
        for name, raw in schema["properties"].items():
            spec = raw if isinstance(raw, dict) else {"type": raw}
            raw_type = spec.get("type", "any")
            output[name] = {
                "type": type_label(raw_type),
                "nullable": nullable(raw_type),
                "required": name in required,
                "default": spec.get("default", MISSING),
            }
    elif isinstance(schema.get("fields"), list):
        fmt = "avro" if schema.get("type") == "record" else "protobuf-json"
        for field in schema["fields"]:
            if not isinstance(field, dict) or "name" not in field:
                raise ValueError("every field entry must be an object with a name")
            raw_type = field.get("type", "unknown")
            if fmt == "avro":
                is_required = "default" not in field and not nullable(raw_type)
            else:
                is_required = not (
                    field.get("optional")
                    or str(field.get("label", "")).lower() in ("optional", "repeated")
                )
            output[str(field["name"])] = {
                "type": type_label(raw_type),
                "nullable": nullable(raw_type),
                "required": is_required,
                "default": field.get("default", MISSING),
            }
    else:
        raise ValueError("unsupported schema; expected properties or fields")
    return fmt, output


def safe(value: Any) -> Any:
    return "<missing>" if value is MISSING else value


def diff(
    old: dict[str, dict[str, Any]], new: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []

    def add(kind: str, field: str, classification: str, **details: Any) -> None:
        changes.append(
            {"kind": kind, "field": field, "classification": classification, **details}
        )

    for name in sorted(set(new) - set(old)):
        classification = (
            "backward-compatible"
            if not new[name]["required"] or new[name]["default"] is not MISSING
            else "breaking"
        )
        add(
            "field-added",
            name,
            classification,
            required=new[name]["required"],
            default=safe(new[name]["default"]),
        )
    for name in sorted(set(old) - set(new)):
        classification = (
            "forward-compatible" if not old[name]["required"] else "breaking"
        )
        add("field-removed", name, classification, was_required=old[name]["required"])
    for name in sorted(set(old) & set(new)):
        before, after = old[name], new[name]
        if before["type"] != after["type"]:
            add("type-changed", name, "breaking", old=before["type"], new=after["type"])
        if before["default"] != after["default"]:
            classification = (
                "breaking"
                if before["default"] is not MISSING
                else "backward-compatible"
            )
            add(
                "default-changed",
                name,
                classification,
                old=safe(before["default"]),
                new=safe(after["default"]),
            )
        if before["nullable"] != after["nullable"]:
            classification = "backward-compatible" if after["nullable"] else "breaking"
            add(
                "nullability-changed",
                name,
                classification,
                old=before["nullable"],
                new=after["nullable"],
            )
        if before["required"] != after["required"]:
            classification = (
                "backward-compatible" if not after["required"] else "breaking"
            )
            add(
                "requiredness-changed",
                name,
                classification,
                old=before["required"],
                new=after["required"],
            )
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("current", type=Path, help="current schema JSON")
    parser.add_argument("proposed", type=Path, help="proposed schema JSON")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        old_fmt, old = normalize(load(args.current))
        new_fmt, new = normalize(load(args.proposed))
        if old_fmt != new_fmt:
            raise ValueError(f"schema formats differ: {old_fmt} vs {new_fmt}")
        changes = diff(old, new)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    breaking = [change for change in changes if change["classification"] == "breaking"]
    report = {
        "format": old_fmt,
        "current": str(args.current),
        "proposed": str(args.proposed),
        "compatible": not breaking,
        "summary": {"changes": len(changes), "breaking": len(breaking)},
        "changes": changes,
    }
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"Schema format: {old_fmt}")
        print(f"Compatibility: {'PASS' if not breaking else 'BREAKING'}")
        for change in changes:
            print(f"- [{change['classification']}] {change['field']}: {change['kind']}")
        if not changes:
            print("- no changes")
    return 1 if breaking else 0


if __name__ == "__main__":
    sys.exit(main())
