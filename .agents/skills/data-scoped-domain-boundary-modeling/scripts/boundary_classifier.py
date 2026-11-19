#!./.venv/bin/python
"""Classify a product capability as FaaS, SaaS, PaaS, or hybrid.

Usage:
  boundary_classifier.py --input "Event-driven image processor"
  cat description.txt | boundary_classifier.py
  boundary_classifier.py --input description.txt --input-file --interactive

The report is written to stdout as JSON. Interactive mode asks for explicit
answers; otherwise conservative keyword evidence is extracted from the text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DIMENSIONS = {
    "statelessness": {
        "positive": (
            "stateless",
            "event",
            "webhook",
            "queue",
            "schedule",
            "short-lived",
            "burst",
        ),
        "negative": ("stateful", "long-running", "persistent connection", "session"),
        "question": "Is execution short-lived, stateless, and triggered by an event/request?",
    },
    "multi_tenancy": {
        "positive": (
            "tenant",
            "customer",
            "organization",
            "workspace",
            "shared application",
        ),
        "negative": ("single user", "single tenant", "internal-only"),
        "question": "Does a managed product serve multiple customer organizations?",
    },
    "self_service": {
        "positive": (
            "self-service",
            "developer platform",
            "deploy",
            "runtime",
            "provision",
            "quota",
        ),
        "negative": ("provider managed", "no infrastructure access", "fixed workflow"),
        "question": "Can customer developers provision or deploy resources within guardrails?",
    },
    "data_ownership": {
        "positive": (
            "customer data",
            "tenant data",
            "system of record",
            "managed data",
            "residency",
        ),
        "negative": ("no storage", "pass-through", "ephemeral"),
        "question": "Does the provider persist and govern tenant data as part of the product?",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--input", help="Product description text, or a path when --input-file is set"
    )
    parser.add_argument(
        "--input-file", action="store_true", help="Treat --input as a UTF-8 file path"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Prompt for yes/no/unknown answers"
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print the JSON report"
    )
    return parser.parse_args()


def read_description(args: argparse.Namespace) -> str:
    if args.input_file:
        if not args.input:
            raise ValueError("--input-file requires --input PATH")
        try:
            return Path(args.input).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ValueError(f"cannot read input file: {exc}") from exc
    if args.input:
        return args.input.strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    try:
        return input("Describe the product or capability: ").strip()
    except EOFError as exc:
        raise ValueError("no product description supplied") from exc


def ask(question: str) -> bool | None:
    while True:
        try:
            answer = input(f"{question} [y/n/u]: ").strip().lower()
        except EOFError as exc:
            raise ValueError("interactive input ended unexpectedly") from exc
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        if answer in {"u", "unknown", ""}:
            return None
        print("Enter y, n, or u.", file=sys.stderr)


def infer_dimension(text: str, config: dict[str, Any]) -> dict[str, Any]:
    lowered = text.lower()
    positive = [
        term
        for term in config["positive"]
        if re.search(rf"\b{re.escape(term)}\b", lowered)
    ]
    negative = [
        term
        for term in config["negative"]
        if re.search(rf"\b{re.escape(term)}\b", lowered)
    ]
    value = True if len(positive) > len(negative) else False if negative else None
    evidence = positive + [f"negated:{term}" for term in negative]
    return {"value": value, "source": "description", "evidence": evidence}


def classify(
    dimensions: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, int], list[str]]:
    value = lambda key: dimensions[key]["value"]
    scores = {"FaaS": 0, "SaaS": 0, "PaaS": 0}
    reasons: list[str] = []
    if value("statelessness") is True:
        scores["FaaS"] += 4
        reasons.append("Stateless, bounded execution strongly favors FaaS.")
    elif value("statelessness") is False:
        scores["SaaS"] += 1
        scores["PaaS"] += 1
        reasons.append("Persistent runtime needs reduce FaaS suitability.")
    if value("multi_tenancy") is True:
        scores["SaaS"] += 3
        scores["PaaS"] += 2
        reasons.append("Multi-tenant delivery supports a managed SaaS or PaaS surface.")
    if value("self_service") is True:
        scores["PaaS"] += 5
        reasons.append("Customer-controlled provisioning is the defining PaaS signal.")
    elif value("self_service") is False:
        scores["SaaS"] += 3
        reasons.append("Provider-managed workflows favor SaaS.")
    if value("data_ownership") is True:
        scores["SaaS"] += 2
        scores["PaaS"] += 1
        reasons.append(
            "Provider governance of tenant data requires a managed product boundary."
        )
    elif value("data_ownership") is False and value("statelessness") is True:
        scores["FaaS"] += 2
        reasons.append("Ephemeral data handling reinforces a FaaS boundary.")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    known = sum(item["value"] is not None for item in dimensions.values())
    if known < 2 or (ranked[0][1] > 0 and ranked[0][1] - ranked[1][1] <= 1):
        result = "hybrid"
        reasons.append(
            "Evidence is mixed or incomplete; classify capabilities independently."
        )
    else:
        result = ranked[0][0]
    return result, scores, reasons


def main() -> int:
    args = parse_args()
    try:
        description = read_description(args)
        if not description:
            raise ValueError("product description is empty")
        dimensions = {
            name: infer_dimension(description, config)
            for name, config in DIMENSIONS.items()
        }
        if args.interactive:
            if not sys.stdin.isatty():
                raise ValueError("--interactive requires a terminal")
            for name, config in DIMENSIONS.items():
                dimensions[name] = {
                    "value": ask(config["question"]),
                    "source": "interactive",
                    "evidence": [config["question"]],
                }
        classification, scores, reasoning = classify(dimensions)
        report = {
            "classification": classification,
            "confidence": round(
                sum(v["value"] is not None for v in dimensions.values())
                / len(dimensions),
                2,
            ),
            "scores": scores,
            "dimensions": dimensions,
            "reasoning": reasoning,
            "description": description,
        }
        json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
