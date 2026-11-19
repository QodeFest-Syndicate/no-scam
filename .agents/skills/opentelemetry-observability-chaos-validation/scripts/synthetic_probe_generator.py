#!./.venv/bin/python
"""Generate YAML uptime-probe definitions from a JSON endpoint inventory.

Usage: ./synthetic_probe_generator.py --endpoints endpoints.json --output probes.yaml
Input may be a list or {"endpoints": [...]}; each item needs url and may define
method, expected_status, expected_latency_ms, headers, and body.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert endpoint metadata to synthetic probe YAML."
    )
    parser.add_argument(
        "--endpoints", required=True, type=Path, help="JSON endpoint inventory"
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Destination YAML file"
    )
    parser.add_argument(
        "--interval", default="60s", help="Check interval (default: 60s)"
    )
    parser.add_argument(
        "--timeout", default="10s", help="Request timeout (default: 10s)"
    )
    return parser.parse_args()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "endpoint"


def build_probe(endpoint: dict, index: int, interval: str, timeout: str) -> dict:
    url = endpoint.get("url")
    parsed = urlparse(str(url or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"endpoint {index}: url must be an absolute HTTP(S) URL")
    method = str(endpoint.get("method", "GET")).upper()
    if method not in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}:
        raise ValueError(f"endpoint {index}: unsupported HTTP method {method}")
    status = int(endpoint.get("expected_status", 200))
    latency = int(endpoint.get("expected_latency_ms", 1000))
    if not 100 <= status <= 599 or latency <= 0:
        raise ValueError(f"endpoint {index}: invalid expected status or latency")
    name = (
        endpoint.get("name") or f"{method.lower()}-{slug(parsed.netloc + parsed.path)}"
    )
    assertions = [
        {"type": "status_code", "operator": "equals", "expected": status},
        {"type": "response_time_ms", "operator": "less_than", "expected": latency},
    ]
    if endpoint.get("expected_body_contains"):
        assertions.append(
            {"type": "body_contains", "expected": endpoint["expected_body_contains"]}
        )
    return {
        "name": str(name),
        "type": "http",
        "enabled": True,
        "schedule": {"interval": interval, "timeout": timeout},
        "request": {
            "url": url,
            "method": method,
            "headers": endpoint.get("headers", {}),
            "body": endpoint.get("body"),
        },
        "assertions": assertions,
        "alerting": {"consecutive_failures": 3, "recovery_successes": 2},
        "labels": {"host": parsed.netloc, "source": "generated"},
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
        payload = json.loads(args.endpoints.read_text(encoding="utf-8"))
        endpoints = payload.get("endpoints") if isinstance(payload, dict) else payload
        if not isinstance(endpoints, list) or not endpoints:
            raise ValueError("input must contain a non-empty endpoint list")
        probes = [
            build_probe(item, i + 1, args.interval, args.timeout)
            for i, item in enumerate(endpoints)
        ]
        document = {
            "apiVersion": "monitoring.qodefest/v1",
            "kind": "SyntheticProbeList",
            "probes": probes,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
        )
        print(f"generated {len(probes)} probes at {args.output}")
    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        yaml.YAMLError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
