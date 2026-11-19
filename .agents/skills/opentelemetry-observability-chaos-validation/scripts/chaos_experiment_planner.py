#!./.venv/bin/python
"""Build bounded chaos-experiment plans from a JSON service topology.

Usage: ./chaos_experiment_planner.py topology.json --output chaos-plan.json
Topology: {"services":[{"name":"api","criticality":"high",
"dependencies":["db"],"replicas":3}]}.
"""

import argparse
import json
import sys
from pathlib import Path

FAILURE_MODES = {
    "latency": {
        "injection": "Add bounded 250–1000 ms dependency latency",
        "observe": "p95 latency, timeouts, retries",
    },
    "error": {
        "injection": "Return a controlled 5xx response rate",
        "observe": "error rate, fallback, circuit breaker",
    },
    "partition": {
        "injection": "Block one dependency direction",
        "observe": "availability, queue depth, consistency",
    },
    "resource_exhaustion": {
        "injection": "Constrain CPU or memory on one replica",
        "observe": "saturation, eviction, rescheduling",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate safe, reviewable chaos experiment plans."
    )
    parser.add_argument("topology", type=Path, help="JSON topology file")
    parser.add_argument(
        "--output", type=Path, help="Output JSON path; defaults to stdout"
    )
    parser.add_argument(
        "--environment",
        default="staging",
        choices=["development", "staging", "production"],
    )
    return parser.parse_args()


def normalize(topology: dict) -> list:
    services = topology.get("services")
    if not isinstance(services, list) or not services:
        raise ValueError("topology must contain a non-empty services list")
    names = set()
    for index, service in enumerate(services, 1):
        if not isinstance(service, dict) or not service.get("name"):
            raise ValueError(f"service {index} must be an object with a name")
        if service["name"] in names:
            raise ValueError(f"duplicate service name: {service['name']}")
        names.add(service["name"])
    return services


def blast_radius(service: dict, dependents: list, environment: str) -> dict:
    criticality = str(service.get("criticality", "medium")).lower()
    replicas = max(1, int(service.get("replicas", 1)))
    target_count = 1
    risk = "high" if criticality == "high" or dependents else "medium"
    return {
        "risk": risk,
        "environment": environment,
        "target_instances": target_count,
        "target_fraction": round(target_count / replicas, 3),
        "direct_dependents": sorted(dependents),
        "constraint": "Never target quorum, all replicas, or multiple dependency layers simultaneously.",
    }


def plan(topology: dict, environment: str) -> dict:
    services = normalize(topology)
    dependents = {item["name"]: [] for item in services}
    for item in services:
        for dependency in item.get("dependencies", []):
            if dependency in dependents:
                dependents[dependency].append(item["name"])

    experiments = []
    for service in services:
        criticality = str(service.get("criticality", "medium")).lower()
        modes = ["latency", "error"]
        if service.get("dependencies"):
            modes.append("partition")
        if int(service.get("replicas", 1)) > 1:
            modes.append("resource_exhaustion")
        for mode in modes:
            detail = FAILURE_MODES[mode]
            experiments.append(
                {
                    "id": f"{service['name']}-{mode}".lower().replace("_", "-"),
                    "target": service["name"],
                    "criticality": criticality,
                    "failure_mode": mode,
                    "injection": detail["injection"],
                    "steady_state_hypothesis": f"The user journey remains within its SLO while one {service['name']} fault is active.",
                    "measurements": [
                        detail["observe"],
                        "SLO burn rate",
                        "healthy replica count",
                    ],
                    "blast_radius": blast_radius(
                        service, dependents[service["name"]], environment
                    ),
                    "preconditions": [
                        "Written authorization recorded",
                        "Dashboards and alerts healthy",
                        "Rollback tested",
                        "No active incident",
                    ],
                    "abort_conditions": [
                        "Fast-burn SLO alert fires",
                        "Healthy capacity falls below redundancy target",
                        "Data integrity is uncertain",
                    ],
                    "rollback": [
                        "Stop fault injection",
                        "Restore network/resource policy",
                        "Verify readiness and backlog recovery",
                        "Run synthetic probe",
                    ],
                    "evidence": [
                        "experiment timestamps",
                        "deployment version",
                        "metrics and trace links",
                        "abort or pass decision",
                    ],
                }
            )
    return {
        "environment": environment,
        "requires_approval": True,
        "experiment_count": len(experiments),
        "experiments": experiments,
    }


def main() -> int:
    args = parse_args()
    try:
        topology = json.loads(args.topology.read_text(encoding="utf-8"))
        rendered = json.dumps(
            plan(topology, args.environment), indent=2, sort_keys=True
        )
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
