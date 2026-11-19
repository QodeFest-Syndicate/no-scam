#!./.venv/bin/python
"""Compare Avro, JSON Schema, or Protobuf-JSON schemas for compatibility.

Usage:
  schema_compatibility_check.py old.json new.json [--format json|text]

Protobuf JSON representation may use ``fields`` as a list of objects containing
``name``, ``type``, ``number``, and optional ``label``/``optional`` attributes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def detect_format(schema: dict[str, Any]) -> str:
    if "$schema" in schema or "properties" in schema:
        return "json-schema"
    fields = schema.get("fields")
    if schema.get("type") == "record" or (
        isinstance(fields, list)
        and any("default" in x for x in fields if isinstance(x, dict))
    ):
        return "avro"
    if isinstance(fields, list) or "messages" in schema:
        return "protobuf-json"
    raise ValueError(
        "unsupported schema shape; expected Avro, JSON Schema, or Protobuf JSON"
    )


def type_name(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(sorted(type_name(x) for x in value))
    if isinstance(value, dict):
        return str(
            value.get("type") or value.get("name") or json.dumps(value, sort_keys=True)
        )
    return str(value)


def normalize(schema: dict[str, Any], fmt: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if fmt == "json-schema":
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError("JSON Schema properties must be an object")
        for name, spec in properties.items():
            spec = spec if isinstance(spec, dict) else {"type": spec}
            types = spec.get("type", "any")
            nullable = "null" in types if isinstance(types, list) else types == "null"
            result[name] = {
                "type": type_name(types),
                "required": name in required,
                "optional": name not in required or nullable,
                "aliases": spec.get("aliases", []),
                "number": None,
            }
    else:
        fields = schema.get("fields", [])
        if not isinstance(fields, list):
            raise ValueError(f"{fmt} fields must be a list")
        for field in fields:
            if not isinstance(field, dict) or "name" not in field:
                raise ValueError(f"invalid {fmt} field entry")
            raw_type = field.get("type", "unknown")
            nullable = isinstance(raw_type, list) and "null" in raw_type
            if fmt == "avro":
                optional = nullable or "default" in field
                required = not optional
            else:
                label = str(field.get("label", "")).lower()
                optional = bool(field.get("optional")) or label in (
                    "optional",
                    "repeated",
                )
                required = not optional
            result[str(field["name"])] = {
                "type": type_name(raw_type),
                "required": required,
                "optional": optional,
                "aliases": field.get("aliases", []),
                "number": field.get("number"),
            }
    return result


def compare(
    old: dict[str, dict[str, Any]], new: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    removed_names = set(old) - set(new)
    added_names = set(new) - set(old)
    renamed: list[dict[str, str]] = []

    for old_name in list(removed_names):
        candidates = []
        for new_name in added_names:
            alias_match = old_name in set(new[new_name].get("aliases", []))
            number_match = old[old_name].get("number") is not None and old[
                old_name
            ].get("number") == new[new_name].get("number")
            if alias_match or number_match:
                candidates.append(new_name)
        if len(candidates) == 1:
            new_name = candidates[0]
            renamed.append({"from": old_name, "to": new_name})
            removed_names.remove(old_name)
            added_names.remove(new_name)

    changes: list[dict[str, Any]] = []
    for name in sorted(set(old) & set(new)):
        if old[name]["type"] != new[name]["type"]:
            changes.append(
                {
                    "kind": "type_changed",
                    "field": name,
                    "old": old[name]["type"],
                    "new": new[name]["type"],
                    "breaking": True,
                }
            )
        if old[name]["optional"] and not new[name]["optional"]:
            changes.append({"kind": "became_required", "field": name, "breaking": True})
    for rename in renamed:
        changes.append({"kind": "renamed", **rename, "breaking": True})
    for name in sorted(removed_names):
        changes.append(
            {
                "kind": "removed",
                "field": name,
                "was_required": old[name]["required"],
                "breaking": bool(old[name]["required"]),
            }
        )
    for name in sorted(added_names):
        changes.append(
            {
                "kind": "added",
                "field": name,
                "optional": new[name]["optional"],
                "breaking": not new[name]["optional"],
            }
        )

    backward_blockers = [
        x
        for x in changes
        if x["kind"] in ("type_changed", "renamed", "became_required")
        or (x["kind"] == "added" and not x["optional"])
    ]
    forward_blockers = [
        x
        for x in changes
        if x["kind"] in ("type_changed", "renamed")
        or (x["kind"] == "removed" and x["was_required"])
    ]
    backward = not backward_blockers
    forward = not forward_blockers
    return {
        "backward_compatible": backward,
        "forward_compatible": forward,
        "full_compatible": backward and forward,
        "changes": changes,
        "backward_blockers": backward_blockers,
        "forward_blockers": forward_blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("old_schema", type=Path, help="previous schema in JSON")
    parser.add_argument("new_schema", type=Path, help="proposed schema in JSON")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        old_doc, new_doc = load(args.old_schema), load(args.new_schema)
        old_fmt, new_fmt = detect_format(old_doc), detect_format(new_doc)
        if old_fmt != new_fmt:
            raise ValueError(f"schema formats differ: {old_fmt} vs {new_fmt}")
        result = compare(normalize(old_doc, old_fmt), normalize(new_doc, new_fmt))
        result.update(
            {
                "format": old_fmt,
                "old_schema": str(args.old_schema),
                "new_schema": str(args.new_schema),
            }
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Format: {result['format']}")
        print(
            f"Backward compatible: {'YES' if result['backward_compatible'] else 'NO'}"
        )
        print(f"Forward compatible:  {'YES' if result['forward_compatible'] else 'NO'}")
        print(f"Full compatible:     {'YES' if result['full_compatible'] else 'NO'}")
        for change in result["changes"]:
            print(f"- {change['kind']}: {json.dumps(change, sort_keys=True)}")
        if not result["changes"]:
            print("- no structural changes detected")
    return 0 if result["full_compatible"] else 1


if __name__ == "__main__":
    sys.exit(main())
