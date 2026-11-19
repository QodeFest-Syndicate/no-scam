#!./.venv/bin/python
"""Calculate an availability SLO's error budget and burn-rate status.

Usage:
  ./slo_calculator.py --target 99.9 --window 30 \
      --current-errors 120 --total-requests 500000
"""

import argparse
import json
import math
import sys


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate SLO burn rate, remaining budget, and alert state.",
        epilog="Exit status is 2 for invalid input; results are emitted as JSON.",
    )
    parser.add_argument(
        "--target",
        type=float,
        required=True,
        help="Availability target percentage, e.g. 99.9",
    )
    parser.add_argument(
        "--window",
        type=positive_float,
        required=True,
        help="SLO evaluation window in days",
    )
    parser.add_argument(
        "--current-errors",
        type=nonnegative_int,
        required=True,
        help="Bad events observed",
    )
    parser.add_argument(
        "--total-requests",
        type=positive_float,
        required=True,
        help="Total eligible events observed",
    )
    return parser.parse_args()


def calculate(target: float, window_days: float, errors: int, total: float) -> dict:
    if not 0 < target < 100:
        raise ValueError("--target must be greater than 0 and less than 100")
    if errors > total:
        raise ValueError("--current-errors cannot exceed --total-requests")

    allowed_ratio = 1.0 - target / 100.0
    observed_ratio = errors / total
    availability = (1.0 - observed_ratio) * 100.0
    allowed_errors = total * allowed_ratio
    remaining_errors = max(0.0, allowed_errors - errors)
    remaining_percent = max(0.0, 100.0 * (1.0 - errors / allowed_errors))
    burn_rate = observed_ratio / allowed_ratio
    errors_per_day = errors / window_days
    exhaustion_days = (
        math.inf if errors_per_day == 0 else remaining_errors / errors_per_day
    )

    # Google SRE-style multi-window thresholds. A single aggregate cannot prove both
    # windows; this reports which policy levels the observed aggregate would breach.
    policies = [
        {
            "severity": "page",
            "long_window": "1h",
            "short_window": "5m",
            "threshold": 14.4,
        },
        {
            "severity": "page",
            "long_window": "6h",
            "short_window": "30m",
            "threshold": 6.0,
        },
        {
            "severity": "ticket",
            "long_window": "3d",
            "short_window": "6h",
            "threshold": 1.0,
        },
    ]
    alerts = [
        dict(policy, breached=burn_rate >= policy["threshold"]) for policy in policies
    ]

    return {
        "inputs": {
            "target_percent": target,
            "window_days": window_days,
            "errors": errors,
            "requests": total,
        },
        "current_availability_percent": round(availability, 6),
        "error_budget": {
            "allowed_errors_at_current_volume": round(allowed_errors, 3),
            "remaining_errors": round(remaining_errors, 3),
            "remaining_percent": round(remaining_percent, 3),
            "exhausted": errors >= allowed_errors,
        },
        "burn_rate": round(burn_rate, 4),
        "time_to_exhaustion_days": None
        if math.isinf(exhaustion_days)
        else round(exhaustion_days, 3),
        "multi_window_alert_policy": alerts,
        "note": "Confirm each alert with independent short- and long-window telemetry before paging.",
    }


def main() -> int:
    args = parse_args()
    try:
        report = calculate(
            args.target, args.window, args.current_errors, args.total_requests
        )
    except (ValueError, ZeroDivisionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
