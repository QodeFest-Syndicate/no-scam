#!./.venv/bin/python
"""Analyze OTLP JSON trace exports for latency, errors, and broken ancestry.

Usage: ./trace_analyzer.py traces.json --top 15 --output report.json
Supports OTLP resourceSpans/scopeSpans and flat JSON span arrays.
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a diagnostic report from OpenTelemetry JSON traces."
    )
    parser.add_argument("input", type=Path, help="OTLP JSON export file")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of slowest spans to include (default: 10)",
    )
    parser.add_argument(
        "--output", type=Path, help="Write JSON report here; defaults to stdout"
    )
    return parser.parse_args()


def attributes(items) -> dict:
    result = {}
    for item in items or []:
        value = item.get("value", {})
        for key in ("stringValue", "intValue", "doubleValue", "boolValue"):
            if key in value:
                result[item.get("key", "")] = value[key]
                break
    return result


def collect_spans(payload) -> list:
    if isinstance(payload, list):
        if all(
            isinstance(item, dict) and ("spanId" in item or "span_id" in item)
            for item in payload
        ):
            return [(item, item.get("serviceName", "unknown")) for item in payload]
        found = []
        for item in payload:
            found.extend(collect_spans(item))
        return found
    if not isinstance(payload, dict):
        return []

    resources = payload.get("resourceSpans") or payload.get("resource_spans")
    if resources is not None:
        found = []
        for resource_span in resources:
            resource = resource_span.get("resource", {})
            service = attributes(resource.get("attributes")).get(
                "service.name", "unknown"
            )
            scopes = (
                resource_span.get("scopeSpans")
                or resource_span.get("scope_spans")
                or []
            )
            for scope in scopes:
                for span in scope.get("spans", []):
                    found.append((span, str(service)))
        return found
    if "spans" in payload and isinstance(payload["spans"], list):
        return [(span, span.get("serviceName", "unknown")) for span in payload["spans"]]

    found = []
    for value in payload.values():
        found.extend(collect_spans(value))
    return found


def first(span: dict, *names, default=None):
    for name in names:
        if name in span:
            return span[name]
    return default


def percentile(values: list, percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percent / 100.0
    lower, upper = math.floor(rank), math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - rank) + ordered[upper] * (rank - lower)


def normalize(entries: list) -> list:
    normalized = []
    for span, service in entries:
        try:
            start = int(first(span, "startTimeUnixNano", "start_time_unix_nano"))
            end = int(first(span, "endTimeUnixNano", "end_time_unix_nano"))
        except (TypeError, ValueError):
            continue
        status = span.get("status") or {}
        code = str(first(status, "code", default="STATUS_CODE_UNSET")).upper()
        normalized.append(
            {
                "trace_id": str(first(span, "traceId", "trace_id", default="")),
                "span_id": str(first(span, "spanId", "span_id", default="")),
                "parent_span_id": str(
                    first(span, "parentSpanId", "parent_span_id", default="")
                ),
                "name": str(span.get("name", "unnamed")),
                "service": service,
                "duration_ms": max(0.0, (end - start) / 1_000_000.0),
                "status": code,
            }
        )
    return normalized


def analyze(spans: list, top: int) -> dict:
    by_service = defaultdict(list)
    ids_by_trace = defaultdict(set)
    for span in spans:
        by_service[span["service"]].append(span["duration_ms"])
        ids_by_trace[span["trace_id"]].add(span["span_id"])

    missing = []
    errors = defaultdict(list)
    for span in spans:
        parent = span["parent_span_id"]
        if parent and parent not in ids_by_trace[span["trace_id"]]:
            missing.append(
                {
                    key: span[key]
                    for key in (
                        "trace_id",
                        "span_id",
                        "parent_span_id",
                        "service",
                        "name",
                    )
                }
            )
        if span["status"] in {"2", "ERROR", "STATUS_CODE_ERROR"}:
            errors[span["trace_id"]].append(
                {
                    "service": span["service"],
                    "span": span["name"],
                    "status": span["status"],
                }
            )

    service_stats = {}
    for service, durations in sorted(by_service.items()):
        service_stats[service] = {
            "span_count": len(durations),
            "p50_ms": round(percentile(durations, 50), 3),
            "p95_ms": round(percentile(durations, 95), 3),
            "p99_ms": round(percentile(durations, 99), 3),
            "max_ms": round(max(durations), 3),
        }
    slowest = sorted(spans, key=lambda item: item["duration_ms"], reverse=True)[:top]
    return {
        "summary": {
            "spans_analyzed": len(spans),
            "services": len(by_service),
            "traces": len(ids_by_trace),
            "traces_with_errors": len(errors),
            "missing_parent_links": len(missing),
        },
        "service_latency": service_stats,
        "slowest_spans": slowest,
        "missing_spans": missing,
        "error_traces": dict(errors),
    }


def main() -> int:
    args = parse_args()
    if args.top < 1:
        print("error: --top must be at least 1", file=sys.stderr)
        return 2
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        spans = normalize(collect_spans(payload))
        if not spans:
            raise ValueError("no spans with valid IDs and timestamps were found")
        rendered = json.dumps(analyze(spans, args.top), indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
