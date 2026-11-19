#!./.venv/bin/python
"""Validate a JSON batch of metering events against a YAML contract.

Usage: ./metering_event_validator.py --contract contract.yaml --events events.json
Contract metrics may be a mapping or list with name/min/max definitions.
"""

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

REQUIRED = ("tenant_id", "metric_name", "value", "timestamp", "idempotency_key")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate metering event fields, ranges, times, metrics, and uniqueness."
    )
    parser.add_argument(
        "--contract", required=True, type=Path, help="YAML metric contract"
    )
    parser.add_argument(
        "--events",
        required=True,
        type=Path,
        help="JSON array or object with events array",
    )
    parser.add_argument(
        "--output", type=Path, help="Output report path; defaults to stdout"
    )
    return parser.parse_args()


def metric_catalog(contract: dict) -> dict:
    metrics = contract.get("metrics", {})
    if isinstance(metrics, dict):
        return {name: (config or {}) for name, config in metrics.items()}
    if isinstance(metrics, list):
        return {
            item["name"]: item
            for item in metrics
            if isinstance(item, dict) and item.get("name")
        }
    raise ValueError("contract.metrics must be a mapping or list")


def parse_time(value) -> dt.datetime:
    text = str(value).replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(dt.UTC)


def validate(events: list, catalog: dict, future_tolerance: int) -> dict:
    now = dt.datetime.now(dt.UTC)
    seen = set()
    results = []
    for index, event in enumerate(events):
        errors = []
        if not isinstance(event, dict):
            results.append(
                {"index": index, "valid": False, "errors": ["event must be an object"]}
            )
            continue
        for field in REQUIRED:
            if field not in event or event[field] in (None, ""):
                errors.append(f"missing required field: {field}")
        key = event.get("idempotency_key")
        if key in seen:
            errors.append("duplicate idempotency_key within batch")
        elif key is not None:
            seen.add(key)
        name = event.get("metric_name")
        config = catalog.get(name)
        if name and config is None:
            errors.append(f"unknown metric_name: {name}")
        try:
            value = float(event.get("value"))
            if not math.isfinite(value):
                raise ValueError
            if (
                config is not None
                and config.get("min") is not None
                and value < float(config["min"])
            ):
                errors.append(f"value below minimum {config['min']}")
            if (
                config is not None
                and config.get("max") is not None
                and value > float(config["max"])
            ):
                errors.append(f"value above maximum {config['max']}")
        except (TypeError, ValueError):
            errors.append("value must be a finite number")
        if event.get("timestamp"):
            try:
                timestamp = parse_time(event["timestamp"])
                if timestamp > now + dt.timedelta(seconds=future_tolerance):
                    errors.append("timestamp is in the future")
            except (TypeError, ValueError):
                errors.append("timestamp must be ISO 8601 with timezone")
        results.append(
            {
                "index": index,
                "idempotency_key": key,
                "valid": not errors,
                "errors": errors,
            }
        )
    invalid = sum(not item["valid"] for item in results)
    return {
        "summary": {
            "total": len(events),
            "valid": len(events) - invalid,
            "invalid": invalid,
        },
        "events": results,
    }


def main() -> int:
    args = parse_args()
    if yaml is None:
        print(
            "error: PyYAML is required (install with: python -m pip install pyyaml)",
            file=sys.stderr,
        )
        return 2
    try:
        contract = yaml.safe_load(args.contract.read_text(encoding="utf-8")) or {}
        payload = json.loads(args.events.read_text(encoding="utf-8"))
        events = payload.get("events") if isinstance(payload, dict) else payload
        if not isinstance(events, list):
            raise ValueError("events input must be an array or contain an events array")
        report = validate(
            events,
            metric_catalog(contract),
            int(contract.get("future_tolerance_seconds", 0)),
        )
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 1 if report["summary"]["invalid"] else 0
    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        yaml.YAMLError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
