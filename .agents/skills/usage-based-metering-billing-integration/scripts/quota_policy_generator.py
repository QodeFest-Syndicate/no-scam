#!./.venv/bin/python
"""Generate JSON quota enforcement rules from YAML pricing tiers.

Usage: ./quota_policy_generator.py tiers.yaml --output quota-policies.json
Expected tiers may be a mapping or list; each tier defines limits by metric.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create quota rules and quota-exceeded webhook schemas."
    )
    parser.add_argument("tiers", type=Path, help="YAML pricing tier definition")
    parser.add_argument("--output", required=True, type=Path, help="Destination JSON")
    return parser.parse_args()


def tier_items(payload: dict) -> list:
    tiers = payload.get("tiers", payload)
    if isinstance(tiers, dict):
        return [(name, config or {}) for name, config in tiers.items()]
    if isinstance(tiers, list):
        return [(item.get("name"), item) for item in tiers if isinstance(item, dict)]
    raise ValueError("tiers must be a mapping or list")


def generate(payload: dict) -> dict:
    policies = []
    for tier_name, tier in tier_items(payload):
        if not tier_name:
            raise ValueError("every tier requires a name")
        limits = tier.get("limits")
        if not isinstance(limits, dict) or not limits:
            raise ValueError(f"tier {tier_name} requires a limits mapping")
        for metric, config in limits.items():
            if not isinstance(config, dict):
                config = {"limit": config}
            limit = config.get("limit")
            if limit is None or float(limit) < 0:
                raise ValueError(
                    f"tier {tier_name}, metric {metric}: limit must be non-negative"
                )
            burst = config.get("burst_allowance", tier.get("burst_allowance", 0))
            overage = config.get("overage_policy", tier.get("overage_policy", "deny"))
            if overage not in {"deny", "allow_and_bill", "throttle", "warn"}:
                raise ValueError(
                    f"tier {tier_name}, metric {metric}: unsupported overage_policy"
                )
            policies.append(
                {
                    "id": f"{tier_name}.{metric}",
                    "tier": tier_name,
                    "metric": metric,
                    "window": config.get("window", "billing_period"),
                    "limit": limit,
                    "burst_allowance": burst,
                    "effective_limit": float(limit) + float(burst),
                    "enforcement": {
                        "mode": config.get("mode", "hard"),
                        "overage_policy": overage,
                        "warning_thresholds_percent": config.get(
                            "warning_thresholds_percent", [80, 100]
                        ),
                    },
                    "consistency": config.get("consistency", "authoritative"),
                }
            )
    webhook_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "QuotaExceededEvent",
        "type": "object",
        "required": [
            "event_id",
            "tenant_id",
            "tier",
            "metric",
            "limit",
            "observed",
            "occurred_at",
            "policy_version",
        ],
        "properties": {
            "event_id": {"type": "string", "minLength": 1},
            "tenant_id": {"type": "string", "minLength": 1},
            "tier": {"type": "string"},
            "metric": {"type": "string"},
            "limit": {"type": "number"},
            "observed": {"type": "number"},
            "occurred_at": {"type": "string", "format": "date-time"},
            "policy_version": {"type": "string"},
            "action": {"enum": ["denied", "throttled", "allowed_overage", "warned"]},
        },
        "additionalProperties": False,
    }
    return {
        "version": str(payload.get("version", "1")),
        "policies": policies,
        "webhooks": {
            "quota_exceeded": {
                "delivery": {
                    "idempotency_field": "event_id",
                    "signature_required": True,
                },
                "payload_schema": webhook_schema,
            }
        },
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
        payload = yaml.safe_load(args.tiers.read_text(encoding="utf-8")) or {}
        result = generate(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"generated {len(result['policies'])} policies at {args.output}")
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
