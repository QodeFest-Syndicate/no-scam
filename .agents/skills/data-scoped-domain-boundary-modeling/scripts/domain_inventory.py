#!./.venv/bin/python
"""Validate a JSON or YAML domain inventory and emit a JSON gap report.

Usage: domain_inventory.py domain.yaml [--pretty] [--strict]

YAML input requires PyYAML. JSON works with the Python standard library.
Strict mode returns exit status 1 when required sections are incomplete.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CHECKS = {
    "bounded_contexts": ("bounded_contexts", "contexts"),
    "data_ownership": ("data_ownership", "data_assets", "ownership"),
    "personas": ("personas", "actors", "users"),
    "regulatory_scope": ("regulatory_scope", "compliance", "regulations"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "spec", type=Path, help="Domain specification (.json, .yaml, or .yml)"
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 when gaps are found"
    )
    return parser.parse_args()


def load_spec(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        elif path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore
            except ImportError as exc:
                raise ValueError(
                    "YAML input requires PyYAML; install it or provide JSON"
                ) from exc
            data = yaml.safe_load(text)
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                try:
                    import yaml  # type: ignore
                except ImportError as exc:
                    raise ValueError(
                        "unknown extension and content is not JSON"
                    ) from exc
                data = yaml.safe_load(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid specification: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("top-level specification must be an object/mapping")
    return data


def first_present(
    spec: dict[str, Any], aliases: tuple[str, ...]
) -> tuple[str | None, Any]:
    for key in aliases:
        if key in spec:
            return key, spec[key]
    return None, None


def populated(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def inspect_details(category: str, value: Any) -> list[str]:
    gaps: list[str] = []
    if category == "bounded_contexts" and isinstance(value, list):
        for index, item in enumerate(value):
            if not isinstance(item, dict) or not item.get("name"):
                gaps.append(f"bounded_contexts[{index}] lacks a name")
            if isinstance(item, dict) and not (item.get("owner") or item.get("team")):
                gaps.append(f"bounded_contexts[{index}] lacks an accountable owner")
    elif category == "data_ownership" and isinstance(value, list):
        for index, item in enumerate(value):
            if not isinstance(item, dict) or not (
                item.get("owner") or item.get("system_of_record")
            ):
                gaps.append(f"data_ownership[{index}] lacks owner/system_of_record")
            if isinstance(item, dict) and not (
                item.get("tenant_key") or item.get("partition_key")
            ):
                gaps.append(f"data_ownership[{index}] lacks tenant/partition key")
    elif category == "personas" and isinstance(value, list):
        for index, item in enumerate(value):
            if not isinstance(item, dict) or not item.get("name"):
                gaps.append(f"personas[{index}] lacks a name")
            if isinstance(item, dict) and not (
                item.get("jobs") or item.get("responsibilities")
            ):
                gaps.append(f"personas[{index}] lacks jobs/responsibilities")
    elif category == "regulatory_scope" and isinstance(value, dict):
        if not any(
            key in value
            for key in ("frameworks", "residency", "retention", "classification")
        ):
            gaps.append(
                "regulatory_scope lacks frameworks, residency, retention, or classification"
            )
    return gaps


def main() -> int:
    args = parse_args()
    try:
        spec = load_spec(args.spec)
        results: dict[str, Any] = {}
        all_gaps: list[str] = []
        for category, aliases in CHECKS.items():
            key, value = first_present(spec, aliases)
            gaps = (
                []
                if populated(value)
                else [f"missing or empty required section: {category}"]
            )
            if not gaps:
                gaps.extend(inspect_details(category, value))
            all_gaps.extend(gaps)
            results[category] = {"complete": not gaps, "source_key": key, "gaps": gaps}
        _, raw_contexts = first_present(spec, CHECKS["bounded_contexts"])
        _, raw_assets = first_present(spec, CHECKS["data_ownership"])
        contexts = (
            [
                {
                    "name": item.get("name", "unnamed"),
                    "owner": item.get("owner") or item.get("team") or "unassigned",
                }
                for item in raw_contexts
                if isinstance(item, dict)
            ]
            if isinstance(raw_contexts, list)
            else []
        )
        ownership = (
            [
                {
                    "asset": item.get("asset")
                    or item.get("name")
                    or item.get("id")
                    or "unnamed",
                    "owner": item.get("owner")
                    or item.get("system_of_record")
                    or "unassigned",
                    "consumers": item.get("consumers", []),
                }
                for item in raw_assets
                if isinstance(item, dict)
            ]
            if isinstance(raw_assets, list)
            else []
        )
        report = {
            "source": str(args.spec),
            "complete": not all_gaps,
            "summary": {
                "checks": len(CHECKS),
                "passed": sum(r["complete"] for r in results.values()),
                "gaps": len(all_gaps),
            },
            "checks": results,
            "gaps": all_gaps,
            "domain_map": {"contexts": contexts, "data_ownership": ownership},
        }
        json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
        sys.stdout.write("\n")
        return 1 if args.strict and all_gaps else 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
