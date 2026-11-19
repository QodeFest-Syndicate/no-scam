#!./.venv/bin/python
"""Estimate pipeline throughput, lag growth, and scaling requirements.

Usage:
  throughput_estimator.py --event-rate 12000 --event-size 2.5 \
    --partitions 12 --consumers 8 --processing-ms 0.8 [--backlog 500000]

Rates are events/second, event size is KiB, and processing time is milliseconds.
The model assumes one active consumer worker per partition and reports a
capacity-planning estimate rather than a hardware benchmark.
"""

import argparse
import json
import math
import sys


def positive(value: str) -> float:
    number = float(value)
    if number <= 0 or not math.isfinite(number):
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return number


def nonnegative(value: str) -> float:
    number = float(value)
    if number < 0 or not math.isfinite(number):
        raise argparse.ArgumentTypeError("must be a non-negative finite number")
    return number


def estimate(
    rate: float,
    size_kib: float,
    partitions: int,
    consumers: int,
    process_ms: float,
    backlog: float,
    target_util: float,
) -> dict[str, float | int | str | None]:
    active_workers = min(partitions, consumers)
    worker_capacity = 1000.0 / process_ms
    theoretical = active_workers * worker_capacity
    sustainable = theoretical * target_util
    processed = min(rate, theoretical)
    lag_growth = max(0.0, rate - theoretical)
    drain_rate = max(0.0, theoretical - rate)
    lag_seconds = backlog / theoretical if theoretical else math.inf
    drain_seconds = (
        backlog / drain_rate
        if backlog and drain_rate
        else (0.0 if not backlog else None)
    )
    ingress_mib = rate * size_kib / 1024.0
    processing_mib = processed * size_kib / 1024.0
    required_workers = max(1, math.ceil(rate / (worker_capacity * target_util)))
    recommended_partitions = max(partitions, required_workers)
    recommended_consumers = min(recommended_partitions, required_workers)
    utilization = rate / theoretical if theoretical else math.inf
    status = (
        "overloaded"
        if rate > theoretical
        else "at-risk"
        if rate > sustainable
        else "healthy"
    )
    return {
        "status": status,
        "source_events_per_second": rate,
        "source_mib_per_second": ingress_mib,
        "active_workers": active_workers,
        "per_worker_capacity_events_per_second": worker_capacity,
        "theoretical_throughput_events_per_second": theoretical,
        "estimated_processed_events_per_second": processed,
        "estimated_processed_mib_per_second": processing_mib,
        "capacity_utilization_percent": utilization * 100.0,
        "lag_growth_events_per_second": lag_growth,
        "lag_growth_events_per_minute": lag_growth * 60.0,
        "current_backlog_events": backlog,
        "backlog_service_time_seconds": lag_seconds,
        "backlog_drain_time_seconds": drain_seconds,
        "recommended_partition_count": recommended_partitions,
        "recommended_consumer_parallelism": recommended_consumers,
        "target_utilization_percent": target_util * 100.0,
    }


def display_number(value: float | str) -> str:
    if isinstance(value, float):
        return "unbounded" if math.isinf(value) else f"{value:,.2f}"
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--event-rate",
        required=True,
        type=positive,
        help="peak source rate in events/second",
    )
    parser.add_argument(
        "--event-size", required=True, type=positive, help="average event size in KiB"
    )
    parser.add_argument(
        "--partitions", required=True, type=int, help="source partition count"
    )
    parser.add_argument(
        "--consumers", required=True, type=int, help="consumer parallelism"
    )
    parser.add_argument(
        "--processing-ms",
        required=True,
        type=positive,
        help="mean processing time per event",
    )
    parser.add_argument(
        "--backlog", type=nonnegative, default=0.0, help="current lag in events"
    )
    parser.add_argument(
        "--target-utilization",
        type=positive,
        default=0.70,
        help="capacity utilization target as a fraction (default: 0.70)",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    if args.partitions <= 0 or args.consumers <= 0:
        parser.error("--partitions and --consumers must be positive integers")
    if not 0 < args.target_utilization < 1:
        parser.error("--target-utilization must be greater than 0 and less than 1")
    try:
        report = estimate(
            args.event_rate,
            args.event_size,
            args.partitions,
            args.consumers,
            args.processing_ms,
            args.backlog,
            args.target_utilization,
        )
    except (ArithmeticError, ValueError) as exc:
        print(f"error: failed to estimate capacity: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        labels = {
            "status": "Status",
            "theoretical_throughput_events_per_second": "Theoretical throughput (events/s)",
            "capacity_utilization_percent": "Capacity utilization (%)",
            "lag_growth_events_per_minute": "Estimated lag growth (events/min)",
            "backlog_drain_time_seconds": "Backlog drain time (s)",
            "recommended_partition_count": "Recommended partitions",
            "recommended_consumer_parallelism": "Recommended consumers",
        }
        for key, label in labels.items():
            print(f"{label}: {display_number(report[key])}")
    return 1 if report["status"] == "overloaded" else 0


if __name__ == "__main__":
    sys.exit(main())
