#!./.venv/bin/python
"""Compare CSV or JSON dataset snapshots and report simple statistical drift.

Usage: ./data_drift_detector.py baseline.csv current.csv --output drift.json
JSON inputs may be an array of records or {"records": [...]}.
"""

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect schema, null-rate, cardinality, and numeric distribution drift."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument(
        "--output", type=Path, help="Output JSON path; defaults to stdout"
    )
    parser.add_argument(
        "--warn",
        type=float,
        default=0.20,
        help="Relative-change warning threshold (default: 0.20)",
    )
    parser.add_argument(
        "--critical",
        type=float,
        default=0.50,
        help="Relative-change critical threshold (default: 0.50)",
    )
    return parser.parse_args()


def load_records(path: Path) -> list:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("records") if isinstance(payload, dict) else payload
        if not isinstance(records, list) or not all(
            isinstance(item, dict) for item in records
        ):
            raise ValueError(f"{path}: JSON must contain an array of objects")
        return records
    raise ValueError(f"{path}: expected .csv or .json")


def is_null(value) -> bool:
    return value is None or (
        isinstance(value, str) and value.strip().lower() in {"", "null", "none", "nan"}
    )


def number(value):
    if is_null(value) or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def summarize(records: list, column: str) -> dict:
    values = [record.get(column) for record in records]
    present = [value for value in values if not is_null(value)]
    numeric = [parsed for value in present if (parsed := number(value)) is not None]
    summary = {
        "rows": len(records),
        "null_rate": len(values) and (len(values) - len(present)) / len(values) or 0.0,
        "cardinality": len(
            {json.dumps(value, sort_keys=True, default=str) for value in present}
        ),
        "top_values": Counter(map(str, present)).most_common(5),
    }
    if present and len(numeric) / len(present) >= 0.9:
        summary["numeric"] = {
            "mean": statistics.fmean(numeric),
            "std": statistics.pstdev(numeric) if len(numeric) > 1 else 0.0,
            "min": min(numeric),
            "max": max(numeric),
        }
    return summary


def relative_change(before: float, after: float) -> float:
    denominator = max(abs(before), 1e-12)
    return abs(after - before) / denominator


def severity(changes: list, warn: float, critical: float) -> str:
    maximum = max(changes, default=0.0)
    return (
        "critical" if maximum >= critical else "warning" if maximum >= warn else "none"
    )


def analyze(baseline: list, current: list, warn: float, critical: float) -> dict:
    if not baseline or not current:
        raise ValueError("both snapshots must contain at least one record")
    old_columns = set().union(*(record.keys() for record in baseline))
    new_columns = set().union(*(record.keys() for record in current))
    columns = {}
    for column in sorted(old_columns & new_columns):
        before, after = summarize(baseline, column), summarize(current, column)
        changes = {
            "null_rate_absolute": abs(after["null_rate"] - before["null_rate"]),
            "cardinality_relative": relative_change(
                before["cardinality"], after["cardinality"]
            ),
        }
        if "numeric" in before and "numeric" in after:
            for metric in ("mean", "std", "min", "max"):
                changes[f"{metric}_relative"] = relative_change(
                    before["numeric"][metric], after["numeric"][metric]
                )
        columns[column] = {
            "severity": severity(list(changes.values()), warn, critical),
            "changes": {key: round(value, 6) for key, value in changes.items()},
            "baseline": before,
            "current": after,
        }
    counts = Counter(item["severity"] for item in columns.values())
    return {
        "summary": {
            "baseline_rows": len(baseline),
            "current_rows": len(current),
            "critical_columns": counts["critical"],
            "warning_columns": counts["warning"],
        },
        "schema": {
            "new_columns": sorted(new_columns - old_columns),
            "missing_columns": sorted(old_columns - new_columns),
        },
        "thresholds": {"warning": warn, "critical": critical},
        "columns": columns,
    }


def main() -> int:
    args = parse_args()
    if not 0 < args.warn < args.critical:
        print("error: thresholds must satisfy 0 < --warn < --critical", file=sys.stderr)
        return 2
    try:
        report = analyze(
            load_records(args.baseline),
            load_records(args.current),
            args.warn,
            args.critical,
        )
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except (OSError, json.JSONDecodeError, csv.Error, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
