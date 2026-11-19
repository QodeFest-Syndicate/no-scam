#!./.venv/bin/python
"""Simulate tenant charges for flat, per-unit, graduated, and volume pricing.

Usage: ./pricing_model_simulator.py usage.json pricing.json --output forecast.json
Usage: {"tenants":{"acme":{"api_calls":[100,120]}}}; pricing defines models.
"""

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project revenue, tenant cost, and breakeven for pricing models."
    )
    parser.add_argument("usage", type=Path)
    parser.add_argument("pricing", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def dec(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"invalid numeric value: {value!r}")


def graduated(quantity: Decimal, tiers: list) -> Decimal:
    charge, previous = Decimal(0), Decimal(0)
    for tier in tiers:
        upper = dec(tier["up_to"]) if tier.get("up_to") is not None else None
        units = (
            max(Decimal(0), quantity - previous)
            if upper is None
            else max(Decimal(0), min(quantity, upper) - previous)
        )
        charge += units * dec(tier["unit_price"])
        if upper is None or quantity <= upper:
            break
        previous = upper
    return charge


def volume(quantity: Decimal, tiers: list) -> Decimal:
    for tier in tiers:
        upper = dec(tier["up_to"]) if tier.get("up_to") is not None else None
        if upper is None or quantity <= upper:
            return quantity * dec(tier["unit_price"])
    raise ValueError("volume pricing requires a final open-ended tier")


def rate(quantity: Decimal, model: dict) -> Decimal:
    kind = model.get("type")
    included = dec(model.get("included", 0))
    billable = max(Decimal(0), quantity - included)
    if kind == "flat":
        return dec(model.get("flat_fee", 0))
    if kind == "per_unit":
        return dec(model.get("base_fee", 0)) + billable * dec(
            model.get("unit_price", 0)
        )
    tiers = model.get("tiers")
    if kind == "tiered" and isinstance(tiers, list):
        return dec(model.get("base_fee", 0)) + graduated(billable, tiers)
    if kind == "volume" and isinstance(tiers, list):
        return dec(model.get("base_fee", 0)) + volume(billable, tiers)
    raise ValueError(f"unsupported or incomplete pricing model: {kind}")


def normalize_usage(payload: dict) -> dict:
    tenants = payload.get("tenants", payload)
    if not isinstance(tenants, dict) or not tenants:
        raise ValueError("usage must contain a non-empty tenants mapping")
    result = {}
    for tenant, metrics in tenants.items():
        if not isinstance(metrics, dict):
            raise ValueError(f"tenant {tenant} usage must be a mapping")
        result[tenant] = {}
        for metric, values in metrics.items():
            sequence = values if isinstance(values, list) else [values]
            result[tenant][metric] = sum((dec(item) for item in sequence), Decimal(0))
    return result


def simulate(usage_payload: dict, pricing: dict) -> dict:
    usage = normalize_usage(usage_payload)
    models = pricing.get("models")
    if not isinstance(models, dict) or not models:
        raise ValueError("pricing must contain a models mapping by metric")
    variable_costs = pricing.get("unit_costs", {})
    tenant_rows, revenue, variable_cost = [], Decimal(0), Decimal(0)
    for tenant, metrics in sorted(usage.items()):
        charges, costs = {}, {}
        for metric, quantity in metrics.items():
            if metric not in models:
                raise ValueError(f"no pricing model for metric {metric}")
            charges[metric] = rate(quantity, models[metric])
            costs[metric] = quantity * dec(variable_costs.get(metric, 0))
        tenant_revenue, tenant_cost = (
            sum(charges.values(), Decimal(0)),
            sum(costs.values(), Decimal(0)),
        )
        revenue += tenant_revenue
        variable_cost += tenant_cost
        tenant_rows.append(
            {
                "tenant_id": tenant,
                "usage": {k: str(v) for k, v in metrics.items()},
                "charges": {
                    k: str(v.quantize(Decimal("0.01"))) for k, v in charges.items()
                },
                "projected_revenue": str(tenant_revenue.quantize(Decimal("0.01"))),
                "variable_cost": str(tenant_cost.quantize(Decimal("0.01"))),
            }
        )
    fixed = dec(pricing.get("fixed_cost", 0))
    contribution = revenue - variable_cost
    average_contribution = contribution / len(usage)
    breakeven_tenants = (
        None
        if average_contribution <= 0
        else int(
            (fixed / average_contribution).to_integral_value(rounding="ROUND_CEILING")
        )
    )
    return {
        "currency": pricing.get("currency", "USD"),
        "tenant_count": len(usage),
        "tenants": tenant_rows,
        "totals": {
            "projected_revenue": str(revenue.quantize(Decimal("0.01"))),
            "variable_cost": str(variable_cost.quantize(Decimal("0.01"))),
            "fixed_cost": str(fixed),
            "projected_profit": str((contribution - fixed).quantize(Decimal("0.01"))),
        },
        "breakeven": {
            "average_contribution_per_tenant": str(
                average_contribution.quantize(Decimal("0.01"))
            ),
            "tenants_required": breakeven_tenants,
        },
    }


def main() -> int:
    args = parse_args()
    try:
        usage = json.loads(args.usage.read_text(encoding="utf-8"), parse_float=Decimal)
        pricing = json.loads(
            args.pricing.read_text(encoding="utf-8"), parse_float=Decimal
        )
        rendered = json.dumps(simulate(usage, pricing), indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
