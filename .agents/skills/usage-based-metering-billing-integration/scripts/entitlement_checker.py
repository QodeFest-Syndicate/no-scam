#!./.venv/bin/python
"""Evaluate a tenant's feature entitlements and metric usage.

Usage: ./entitlement_checker.py --tenant-id acme --entitlements plans.json \
  --current-usage usage.json
Files may be tenant-keyed mappings or direct feature/limit objects.
"""

import argparse
import json
import math
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report limit state and effective feature flags for a tenant."
    )
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--entitlements", required=True, type=Path)
    parser.add_argument("--current-usage", required=True, type=Path)
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Approaching-limit percentage (default: 80)",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def tenant_view(payload: dict, tenant_id: str) -> dict:
    tenants = payload.get("tenants") if isinstance(payload, dict) else None
    if isinstance(tenants, dict):
        if tenant_id not in tenants:
            raise ValueError(f"tenant {tenant_id!r} not found")
        return tenants[tenant_id]
    if tenant_id in payload and isinstance(payload[tenant_id], dict):
        return payload[tenant_id]
    return payload


def evaluate(entitlements: dict, usage: dict, threshold: float) -> dict:
    limits = entitlements.get("limits", {})
    features = entitlements.get("features", entitlements.get("feature_flags", {}))
    current = usage.get("usage", usage)
    if (
        not isinstance(limits, dict)
        or not isinstance(current, dict)
        or not isinstance(features, dict)
    ):
        raise ValueError("limits, usage, and features must be mappings")
    metrics, overall = [], "within_limits"
    rank = {"within_limits": 0, "approaching_limit": 1, "exceeded": 2}
    for metric, raw_limit in sorted(limits.items()):
        config = raw_limit if isinstance(raw_limit, dict) else {"limit": raw_limit}
        limit = float(config.get("limit"))
        observed = float(current.get(metric, 0))
        if not all(map(math.isfinite, (limit, observed))) or limit < 0 or observed < 0:
            raise ValueError(f"metric {metric} has an invalid limit or usage")
        percent = (
            100.0
            if limit == 0 and observed
            else (0.0 if limit == 0 else observed / limit * 100)
        )
        status = (
            "exceeded"
            if observed > limit
            else "approaching_limit"
            if percent >= threshold
            else "within_limits"
        )
        if rank[status] > rank[overall]:
            overall = status
        metrics.append(
            {
                "metric": metric,
                "usage": observed,
                "limit": limit,
                "remaining": max(0.0, limit - observed),
                "percent_used": round(percent, 3),
                "status": status,
                "overage_policy": config.get("overage_policy", "deny"),
            }
        )
    feature_rows = [
        {
            "feature": name,
            "enabled": bool(
                value.get("enabled", False) if isinstance(value, dict) else value
            ),
            "configuration": value if isinstance(value, dict) else {},
        }
        for name, value in sorted(features.items())
    ]
    return {
        "status": overall,
        "metrics": metrics,
        "features": feature_rows,
        "policy_version": entitlements.get("version"),
        "expires_at": entitlements.get("expires_at"),
    }


def main() -> int:
    args = parse_args()
    if not 0 < args.threshold <= 100:
        print("error: --threshold must be in (0, 100]", file=sys.stderr)
        return 2
    try:
        entitlements = tenant_view(
            json.loads(args.entitlements.read_text(encoding="utf-8")), args.tenant_id
        )
        usage = tenant_view(
            json.loads(args.current_usage.read_text(encoding="utf-8")), args.tenant_id
        )
        report = {
            "tenant_id": args.tenant_id,
            **evaluate(entitlements, usage, args.threshold),
        }
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 1 if report["status"] == "exceeded" else 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
