#!./.venv/bin/python
"""Recommend execute/reuse/compress/skip decisions for stages S1-S8.

Usage: python stage_skip_evaluator.py preconditions.json [--format text|json]
Recognized booleans include has_existing_spec, has_architecture, is_internal_only,
has_existing_tests, changes_data, changes_security, production_release, and docs_only.
"""

import argparse
import json
import sys
from pathlib import Path

STAGES = {
    "S1": "Domain and data scoping",
    "S2": "Architecture and TDD planning",
    "S3": "Task decomposition and routing",
    "S4": "Pre-implementation gate",
    "S5": "Implementation",
    "S6": "Integration and CI/CD",
    "S7": "Validation and observability",
    "S8": "Delivery and GTM",
}


def decide(stage, f):
    high_risk = (
        f.get("changes_data")
        or f.get("changes_security")
        or f.get("production_release")
    )
    if stage == "S1":
        if f.get("has_domain_scope") and not f.get("changes_data"):
            return (
                "reuse",
                "Validated domain/data scope exists and data boundaries are unchanged.",
            )
        if f.get("docs_only"):
            return "compress", "Confirm scope and terminology only."
    if stage == "S2":
        if (
            f.get("has_existing_spec")
            and f.get("has_architecture")
            and not f.get("architecture_change")
        ):
            return "reuse", "Current specification and architecture are available."
        if f.get("small_change") and not high_risk:
            return "compress", "Use a bounded design note and targeted tests."
    if stage == "S3" and f.get("single_atomic_task"):
        return "compress", "A single atomic task needs no multi-node routing."
    if stage == "S4":
        if high_risk:
            return (
                "execute",
                "Mandatory risk gate for data, security, or production change.",
            )
        if f.get("docs_only"):
            return "compress", "Verify document quality and links only."
    if stage == "S5" and f.get("analysis_only"):
        return "skip", "No runtime or repository implementation is requested."
    if stage == "S6":
        if f.get("analysis_only") or (f.get("docs_only") and f.get("is_internal_only")):
            return "skip", "No deployable artifact or runtime integration exists."
        if f.get("has_existing_tests") and f.get("small_change"):
            return "compress", "Run the focused existing pipeline."
    if stage == "S7":
        if f.get("analysis_only"):
            return (
                "compress",
                "Validate conclusions and evidence rather than runtime behavior.",
            )
        if f.get("has_existing_tests"):
            return (
                "reuse",
                "Existing tests may be reused if current and scoped; retain fresh results.",
            )
    if stage == "S8":
        if f.get("is_internal_only") and not f.get("production_release"):
            return "skip", "Internal-only work has no external delivery or GTM output."
        if f.get("docs_only"):
            return (
                "compress",
                "Publish reviewed documentation without deployment activities.",
            )
    return (
        "execute",
        "Required artifact or equivalent validated evidence was not supplied.",
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("preconditions", type=Path)
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    try:
        flags = json.loads(a.preconditions.read_text(encoding="utf-8"))
        if not isinstance(flags, dict):
            raise ValueError("input must be a JSON object")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    decisions = [
        {
            "stage": stage,
            "name": name,
            "decision": decide(stage, flags)[0],
            "justification": decide(stage, flags)[1],
        }
        for stage, name in STAGES.items()
    ]
    sequence = [d["stage"] for d in decisions if d["decision"] != "skip"]
    payload = {
        "recommended_sequence": sequence,
        "decisions": decisions,
        "warning": "Never skip a policy-mandated gate; verify evidence currency and scope.",
    }
    if a.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print("Recommended sequence: " + " -> ".join(sequence))
        for d in decisions:
            print(
                f"{d['stage']} {d['decision'].upper():8} {d['name']}: {d['justification']}"
            )
        print("\n" + payload["warning"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
