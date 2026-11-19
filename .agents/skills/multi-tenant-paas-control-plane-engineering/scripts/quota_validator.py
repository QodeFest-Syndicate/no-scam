#!./.venv/bin/python
"""Validate tenant quota JSON/YAML against cluster capacity and tier policy.

Usage: quota_validator.py tenant-quota.yaml [--cluster-capacity JSON] [--strict]

Expected keys: tier, quotas.cpu, quotas.memory, quotas.storage, and optionally
sla.availability. YAML input requires PyYAML; JSON uses only the stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TIER_LIMITS = {
    "free": {
        "cpu": 2.0,
        "memory": 4 * 1024**3,
        "storage": 20 * 1024**3,
        "availability": 99.0,
    },
    "pro": {
        "cpu": 16.0,
        "memory": 32 * 1024**3,
        "storage": 500 * 1024**3,
        "availability": 99.9,
    },
    "enterprise": {
        "cpu": 64.0,
        "memory": 128 * 1024**3,
        "storage": 2 * 1024**4,
        "availability": 99.95,
    },
}
DEFAULT_CAPACITY = {"cpu": 256.0, "memory": 1024 * 1024**3, "storage": 20 * 1024**4}
UNITS = {
    "Ki": 1024,
    "Mi": 1024**2,
    "Gi": 1024**3,
    "Ti": 1024**4,
    "K": 1000,
    "M": 1000**2,
    "G": 1000**3,
    "T": 1000**4,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("config", type=Path)
    parser.add_argument(
        "--cluster-capacity",
        help="JSON object with cpu, memory, and storage quantities",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 when validation errors exist"
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON report"
    )
    return parser.parse_args()


def load_mapping(path: Path) -> dict[str, Any]:
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
                    "YAML input requires PyYAML; provide JSON or install PyYAML"
                ) from exc
            data = yaml.safe_load(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid config: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("configuration must be an object/mapping")
    return data


def quantity(value: Any, resource: str) -> float:
    text = str(value).strip()
    if resource == "cpu" and text.endswith("m"):
        number = float(text[:-1]) / 1000
    else:
        match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))([A-Za-z]*)", text)
        if not match:
            raise ValueError(f"invalid {resource} quantity: {value}")
        number = float(match.group(1))
        suffix = match.group(2)
        if suffix:
            if suffix not in UNITS:
                raise ValueError(f"unsupported {resource} unit: {suffix}")
            number *= UNITS[suffix]
    return number


def normalized_capacity(raw: dict[str, Any]) -> dict[str, float]:
    return {key: quantity(raw[key], key) for key in ("cpu", "memory", "storage")}


def main() -> int:
    args = parse_args()
    try:
        config = load_mapping(args.config)
        tier = config.get("tier")
        if tier not in TIER_LIMITS:
            raise ValueError("tier must be free, pro, or enterprise")
        quotas = config.get("quotas")
        if not isinstance(quotas, dict):
            raise ValueError("quotas must be an object with cpu, memory, and storage")
        capacity_raw = (
            json.loads(args.cluster_capacity)
            if args.cluster_capacity
            else config.get("platform_limits", DEFAULT_CAPACITY)
        )
        if not isinstance(capacity_raw, dict):
            raise ValueError("cluster capacity must be a JSON object")
        missing = [
            key
            for key in ("cpu", "memory", "storage")
            if key not in quotas or key not in capacity_raw
        ]
        if missing:
            raise ValueError(f"missing quantities: {', '.join(sorted(set(missing)))}")
        actual = {
            key: quantity(quotas[key], key) for key in ("cpu", "memory", "storage")
        }
        capacity = normalized_capacity(capacity_raw)
        findings = []
        for key, value in actual.items():
            if value < 0:
                findings.append(
                    {
                        "severity": "error",
                        "field": key,
                        "message": "quota may not be negative",
                    }
                )
            if value > capacity[key]:
                findings.append(
                    {
                        "severity": "error",
                        "field": key,
                        "message": "quota exceeds cluster capacity",
                    }
                )
            if value > TIER_LIMITS[tier][key]:
                findings.append(
                    {
                        "severity": "error",
                        "field": key,
                        "message": f"quota exceeds {tier} tier maximum",
                    }
                )
        availability = (
            config.get("sla", {}).get("availability")
            if isinstance(config.get("sla"), dict)
            else None
        )
        expected = TIER_LIMITS[tier]["availability"]
        if availability is None:
            findings.append(
                {
                    "severity": "warning",
                    "field": "sla.availability",
                    "message": f"declare tier SLA ({expected}% expected)",
                }
            )
        elif float(str(availability).rstrip("%")) != expected:
            findings.append(
                {
                    "severity": "error",
                    "field": "sla.availability",
                    "message": f"must equal {expected}% for {tier} tier",
                }
            )
        report = {
            "valid": not any(f["severity"] == "error" for f in findings),
            "tier": tier,
            "normalized": {"quotas": actual, "cluster_capacity": capacity},
            "findings": findings,
        }
        json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
        sys.stdout.write("\n")
        return 1 if args.strict and not report["valid"] else 0
    except (ValueError, TypeError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
