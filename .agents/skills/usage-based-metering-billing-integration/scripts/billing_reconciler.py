#!./.venv/bin/python
"""Reconcile metered usage against billed invoice line items.

Usage: ./billing_reconciler.py usage.csv invoices.json --tolerance-percent 1
Records need tenant_id, metric_name, and amount (or usage/quantity).
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report over/under billing, missing tenants, and unmatched lines."
    )
    parser.add_argument("metered", type=Path)
    parser.add_argument("billed", type=Path)
    parser.add_argument(
        "--tolerance-percent",
        type=Decimal,
        default=Decimal("0.01"),
        help="Allowed deviation percent",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def load(path: Path) -> list:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
        rows = next(
            (
                payload[key]
                for key in ("records", "usage", "invoices", "line_items")
                if isinstance(payload, dict) and key in payload
            ),
            payload,
        )
        if not isinstance(rows, list):
            raise ValueError(f"{path}: expected an array of records")
        return rows
    raise ValueError(f"{path}: expected CSV or JSON")


def amount(row: dict) -> Decimal:
    value = next(
        (
            row[key]
            for key in ("amount", "billed_amount", "usage", "quantity", "value")
            if key in row
        ),
        None,
    )
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"invalid amount in row: {row}")


def aggregate(rows: list) -> dict:
    totals = defaultdict(Decimal)
    for index, row in enumerate(rows, 1):
        if (
            not isinstance(row, dict)
            or not row.get("tenant_id")
            or not row.get("metric_name")
        ):
            raise ValueError(f"row {index} requires tenant_id and metric_name")
        totals[(str(row["tenant_id"]), str(row["metric_name"]))] += amount(row)
    return totals


def reconcile(metered: dict, billed: dict, tolerance: Decimal) -> dict:
    lines = []
    keys = sorted(set(metered) | set(billed))
    for tenant, metric in keys:
        expected, actual = metered.get((tenant, metric)), billed.get((tenant, metric))
        if expected is None:
            status, deviation = "unmatched_billed_line", None
        elif actual is None:
            status, deviation = "missing_billed_line", None
        else:
            difference = actual - expected
            deviation = (
                abs(difference / expected * 100)
                if expected
                else (Decimal(0) if actual == 0 else Decimal("Infinity"))
            )
            if deviation <= tolerance:
                status = "matched"
            else:
                status = "over_billed" if difference > 0 else "under_billed"
        lines.append(
            {
                "tenant_id": tenant,
                "metric_name": metric,
                "metered": str(expected) if expected is not None else None,
                "billed": str(actual) if actual is not None else None,
                "deviation_percent": str(deviation) if deviation is not None else None,
                "status": status,
            }
        )
    missing_tenants = sorted(
        {tenant for tenant, _ in metered} - {tenant for tenant, _ in billed}
    )
    extra_tenants = sorted(
        {tenant for tenant, _ in billed} - {tenant for tenant, _ in metered}
    )
    counts = defaultdict(int)
    for line in lines:
        counts[line["status"]] += 1
    return {
        "summary": {"line_items": len(lines), **dict(counts)},
        "missing_tenants": missing_tenants,
        "unmatched_billed_tenants": extra_tenants,
        "line_items": lines,
    }


def main() -> int:
    args = parse_args()
    if args.tolerance_percent < 0:
        print("error: tolerance cannot be negative", file=sys.stderr)
        return 2
    try:
        report = reconcile(
            aggregate(load(args.metered)),
            aggregate(load(args.billed)),
            args.tolerance_percent,
        )
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        discrepancies = sum(
            value
            for key, value in report["summary"].items()
            if key not in {"line_items", "matched"}
        )
        return 1 if discrepancies else 0
    except (OSError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
