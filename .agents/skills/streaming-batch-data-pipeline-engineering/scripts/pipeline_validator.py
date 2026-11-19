#!./.venv/bin/python
"""Validate a YAML or JSON pipeline definition against operational safety rules.

Usage:
  pipeline_validator.py pipeline.yaml [--format text|json] [--strict]

The expected document contains ``sources``, ``stages``, and ``sinks`` lists.
Stage connectivity may be expressed with ``inputs``/``outputs`` or ``depends_on``.
The validator accepts common key aliases so it can audit existing definitions.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_document(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    try:
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
    except Exception as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("pipeline root must be an object")
    return data


def named_items(value: Any, section: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        result = []
        for name, config in value.items():
            item = dict(config) if isinstance(config, dict) else {"value": config}
            item.setdefault("name", name)
            result.append(item)
        return result
    if isinstance(value, list):
        result = []
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                raise ValueError(f"{section}[{index}] must be an object")
            result.append(item)
        return result
    raise ValueError(f"{section} must be a list or object")


def item_name(item: dict[str, Any], index: int, prefix: str) -> str:
    return str(item.get("name") or item.get("id") or f"{prefix}[{index}]")


def enabled(config: Any) -> bool:
    if isinstance(config, bool):
        return config
    if isinstance(config, dict):
        return config.get("enabled", True) is not False
    return config is not None


def validate(data: dict[str, Any]) -> list[dict[str, Any]]:
    sources = named_items(data.get("sources"), "sources")
    stages = named_items(data.get("stages") or data.get("processors"), "stages")
    sinks = named_items(data.get("sinks"), "sinks")

    missing_schema = [
        item_name(x, i, "source")
        for i, x in enumerate(sources)
        if not any(
            x.get(k) for k in ("schema_ref", "schema-ref", "schema", "schemaReference")
        )
    ]
    missing_idempotency = [
        item_name(x, i, "sink")
        for i, x in enumerate(sinks)
        if not enabled(
            x.get("idempotency")
            or x.get("idempotency_config")
            or x.get("deduplication")
            or x.get("upsert_key")
        )
    ]

    source_names = {item_name(x, i, "source") for i, x in enumerate(sources)}
    stage_names = {item_name(x, i, "stage") for i, x in enumerate(stages)}
    sink_names = {item_name(x, i, "sink") for i, x in enumerate(sinks)}
    all_names = source_names | stage_names | sink_names
    referenced: set[str] = set()
    unknown: set[str] = set()
    connected: set[str] = set()
    for i, stage in enumerate(stages):
        name = item_name(stage, i, "stage")
        links = []
        for key in ("inputs", "outputs", "depends_on", "next"):
            value = stage.get(key, [])
            links.extend(value if isinstance(value, list) else [value] if value else [])
        for link in map(str, links):
            referenced.add(link)
            connected.add(name)
            if link in all_names:
                connected.add(link)
            else:
                unknown.add(link)
    for collection in (sources, sinks):
        for item in collection:
            for key in ("inputs", "outputs", "depends_on"):
                value = item.get(key, [])
                links = value if isinstance(value, list) else [value] if value else []
                for link in map(str, links):
                    referenced.add(link)
                    connected.add(str(item.get("name") or item.get("id") or ""))
                    if link in all_names:
                        connected.add(link)
                    else:
                        unknown.add(link)
    orphaned = sorted(stage_names - connected) if stages else []

    backpressure = data.get("backpressure") or data.get("flow_control")
    if not backpressure:
        backpressure = next(
            (x.get("backpressure") for x in stages if x.get("backpressure")), None
        )
    checkpoint = data.get("checkpointing") or data.get("checkpoints")
    if checkpoint is None:
        checkpoint = next(
            (x.get("checkpointing") for x in stages if "checkpointing" in x), None
        )

    def rule(
        rule_id: str, passed: bool, message: str, details: Any = None
    ) -> dict[str, Any]:
        result = {"rule": rule_id, "passed": passed, "message": message}
        if details:
            result["details"] = details
        return result

    return [
        rule(
            "source-schema-reference",
            not missing_schema,
            "Every source has a schema reference"
            if not missing_schema
            else "Sources are missing schema references",
            missing_schema,
        ),
        rule(
            "sink-idempotency",
            not missing_idempotency,
            "Every sink defines idempotency"
            if not missing_idempotency
            else "Sinks are missing idempotency configuration",
            missing_idempotency,
        ),
        rule(
            "stage-connectivity",
            not orphaned and not unknown,
            "All stages are connected and references resolve"
            if not orphaned and not unknown
            else "Pipeline contains orphaned stages or unknown links",
            {"orphaned": orphaned, "unknown_references": sorted(unknown)},
        ),
        rule(
            "backpressure-strategy",
            bool(backpressure),
            "Backpressure strategy is defined"
            if backpressure
            else "No backpressure strategy is defined",
        ),
        rule(
            "checkpointing-enabled",
            enabled(checkpoint),
            "Checkpointing is enabled"
            if enabled(checkpoint)
            else "Checkpointing is absent or disabled",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "pipeline", type=Path, help="pipeline definition (.yaml, .yml, or .json)"
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text", help="report format"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail if sources, stages, or sinks are empty",
    )
    args = parser.parse_args()
    try:
        data = load_document(args.pipeline)
        results = validate(data)
        if args.strict:
            for section in ("sources", "stages", "sinks"):
                if not data.get(section):
                    results.append(
                        {
                            "rule": f"non-empty-{section}",
                            "passed": False,
                            "message": f"{section} must not be empty in strict mode",
                        }
                    )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    passed = all(result["passed"] for result in results)
    report = {"pipeline": str(args.pipeline), "passed": passed, "rules": results}
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        for result in results:
            print(
                f"[{'PASS' if result['passed'] else 'FAIL'}] {result['rule']}: {result['message']}"
            )
            if result.get("details"):
                print(f"       {json.dumps(result['details'], sort_keys=True)}")
        print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
