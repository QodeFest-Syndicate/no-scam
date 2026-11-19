#!./.venv/bin/python
"""Recommend a rollout strategy from service risk and delivery constraints.

Usage: python rollout_strategy_selector.py [--criticality high --rollback-minutes 2
       --traffic steady --coverage high --statefulness stateless]
Missing values are prompted interactively; use all flags for automation.
"""

import argparse
import json
import sys


def ask(value, prompt, choices, cast=str):
    if value is not None:
        return value
    if not sys.stdin.isatty():
        raise ValueError(f"missing required input: {prompt}")
    while True:
        raw = input(f"{prompt} ({'/'.join(map(str, choices))}): ").strip().lower()
        try:
            converted = cast(raw)
        except ValueError:
            continue
        if converted in choices:
            return converted


def select(c, rollback, traffic, coverage, state):
    reasons = []
    if state == "stateful" and rollback <= 5:
        strategy = "blue-green"
        reasons.append("fast rollback with isolated old/new environments")
    elif c == "high" and coverage != "low" and traffic != "low":
        strategy = "canary"
        reasons.append(
            "high criticality benefits from metric-gated incremental exposure"
        )
    elif coverage == "low" and c == "high":
        strategy = "blue-green"
        reasons.append(
            "full pre-cutover environment validation is safer than an under-observed canary"
        )
    elif c == "low" and rollback >= 30 and traffic == "low":
        strategy = "recreate"
        reasons.append(
            "low risk and tolerant rollback window reduce duplicate-capacity value"
        )
    else:
        strategy = "rolling"
        reasons.append(
            "balanced availability and capacity without duplicate full environments"
        )
    config = {
        "canary": {
            "traffic_steps": [1, 5, 25, 50, 100],
            "observation_minutes": 15,
            "abort": "error/latency/SLO threshold breach or missing telemetry",
        },
        "blue-green": {
            "cutover": "atomic or 10/50/100%",
            "rollback_window_minutes": max(rollback, 30),
            "requirement": "expand-contract schema compatibility",
        },
        "rolling": {
            "max_unavailable": "0 for high criticality, otherwise 25%",
            "max_surge": "25%",
            "requirement": "readiness and backward compatibility",
        },
        "recreate": {
            "downtime_expected": True,
            "requirement": "maintenance window, backup, smoke test, rollback artifact",
        },
    }[strategy]
    if state == "stateful":
        reasons.append(
            "database changes require expand-contract migration and independent data recovery"
        )
    if traffic == "bursty":
        reasons.append("promotion windows need minimum sample size, not time alone")
    return {"strategy": strategy, "reasons": reasons, "configuration": config}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--criticality", choices=("low", "medium", "high"))
    p.add_argument("--rollback-minutes", type=int)
    p.add_argument("--traffic", choices=("low", "steady", "bursty"))
    p.add_argument("--coverage", choices=("low", "medium", "high"))
    p.add_argument("--statefulness", choices=("stateless", "stateful"))
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    try:
        c = ask(a.criticality, "Criticality", ("low", "medium", "high"))
        r = ask(
            a.rollback_minutes,
            "Required rollback time in minutes",
            tuple(range(1, 121)),
            int,
        )
        t = ask(a.traffic, "Traffic pattern", ("low", "steady", "bursty"))
        v = ask(a.coverage, "Test coverage", ("low", "medium", "high"))
        s = ask(a.statefulness, "State model", ("stateless", "stateful"))
        if r < 1 or r > 120:
            raise ValueError("rollback-minutes must be between 1 and 120")
        result = select(c, r, t, v, s)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if a.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Recommended strategy: {result['strategy']}")
        print("Reasons: " + "; ".join(result["reasons"]))
        print("Configuration:")
        [print(f"- {k}: {v}") for k, v in result["configuration"].items()]
    return 0


if __name__ == "__main__":
    sys.exit(main())
