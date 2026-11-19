#!./.venv/bin/python
"""Validate a YAML/JSON data contract against a practical meta-schema.

Usage:
  contract_validator.py contract.yaml [--format json|text] [--base-dir DIR]

Required contract fields are owner, schema-ref, SLA, quality rules, version, and
a complete consumer registry. Schema references are checked as local files or
HTTP(S) URIs.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SEMVER = re.compile(
    r"^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def load(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            try:
                import yaml  # type: ignore
            except ImportError as exc:
                raise ValueError(
                    "YAML input requires PyYAML; use JSON or install pyyaml"
                ) from exc
            data = yaml.safe_load(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("contract root must be an object")
    return data


def first(data: dict[str, Any], *keys: str) -> Any:
    return next((data[key] for key in keys if key in data), None)


def validate(data: dict[str, Any], base_dir: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(rule: str, passed: bool, message: str, location: str = "") -> None:
        checks.append(
            {"rule": rule, "passed": passed, "message": message, "location": location}
        )

    owner = first(data, "owner", "ownership")
    owner_ok = bool(owner) and (
        not isinstance(owner, dict) or bool(first(owner, "team", "name", "email"))
    )
    add(
        "owner-required",
        owner_ok,
        "Owner is defined" if owner_ok else "Missing accountable owner",
        "owner",
    )

    schema_ref = first(data, "schema-ref", "schema_ref", "schemaRef", "schema")
    schema_ref_ok = isinstance(schema_ref, str) and bool(schema_ref.strip())
    add(
        "schema-reference-required",
        schema_ref_ok,
        "Schema reference is defined" if schema_ref_ok else "Missing schema reference",
        "schema-ref",
    )
    if schema_ref_ok:
        parsed = urlparse(schema_ref)
        if parsed.scheme in ("http", "https"):
            valid_ref, detail = (
                bool(parsed.netloc),
                "Remote schema URI is syntactically valid",
            )
        elif parsed.scheme and parsed.scheme != "file":
            valid_ref, detail = False, f"Unsupported schema URI scheme: {parsed.scheme}"
        else:
            target = (
                Path(parsed.path)
                if Path(parsed.path).is_absolute()
                else base_dir / parsed.path
            )
            valid_ref, detail = (
                target.is_file(),
                f"Local schema {'exists' if target.is_file() else 'not found'}: {target}",
            )
        add("schema-reference-valid", valid_ref, detail, "schema-ref")

    version = first(data, "version", "contract-version", "contract_version")
    version_ok = isinstance(version, str) and bool(SEMVER.fullmatch(version))
    add(
        "version-format",
        version_ok,
        "Version follows semantic versioning"
        if version_ok
        else "Version must be SemVer (for example 1.2.0)",
        "version",
    )

    sla = first(data, "sla", "SLA", "service-levels", "service_levels")
    sla_ok = isinstance(sla, dict) and any(
        key in sla for key in ("freshness", "availability", "completeness", "latency")
    )
    add(
        "sla-required",
        sla_ok,
        "SLA contains measurable objectives"
        if sla_ok
        else "SLA must define at least one measurable objective",
        "sla",
    )

    quality = first(data, "quality-rules", "quality_rules", "qualityRules", "quality")
    quality_ok = isinstance(quality, (list, dict)) and len(quality) > 0
    add(
        "quality-rules-required",
        quality_ok,
        "Quality rules are defined"
        if quality_ok
        else "At least one quality rule is required",
        "quality-rules",
    )

    consumers = first(data, "consumers", "consumer-registry", "consumer_registry")
    registry_ok = isinstance(consumers, list) and len(consumers) > 0
    add(
        "consumer-registry-required",
        registry_ok,
        "Consumer registry is present"
        if registry_ok
        else "Consumer registry must be a non-empty list",
        "consumers",
    )
    if isinstance(consumers, list):
        for index, consumer in enumerate(consumers):
            complete = (
                isinstance(consumer, dict)
                and bool(first(consumer, "name", "id", "service"))
                and bool(first(consumer, "owner", "contact"))
            )
            add(
                "consumer-entry-complete",
                complete,
                "Consumer entry has identity and owner/contact"
                if complete
                else "Consumer entry requires identity and owner/contact",
                f"consumers[{index}]",
            )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "contract", type=Path, help="contract .yaml, .yml, or .json file"
    )
    parser.add_argument(
        "--base-dir", type=Path, help="base directory for relative schema references"
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()
    try:
        data = load(args.contract)
        checks = validate(data, (args.base_dir or args.contract.parent).resolve())
    except ValueError as exc:
        print(
            json.dumps({"passed": False, "error": str(exc)})
            if args.format == "json"
            else f"error: {exc}",
            file=sys.stderr,
        )
        return 2
    passed = all(check["passed"] for check in checks)
    report = {
        "contract": str(args.contract),
        "passed": passed,
        "summary": {
            "passed": sum(check["passed"] for check in checks),
            "failed": sum(not check["passed"] for check in checks),
        },
        "checks": checks,
    }
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        for check in checks:
            print(
                f"[{'PASS' if check['passed'] else 'FAIL'}] {check['rule']} {check['location']}: {check['message']}"
            )
        print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
