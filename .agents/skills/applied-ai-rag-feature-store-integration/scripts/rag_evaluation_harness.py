#!./.venv/bin/python
"""Evaluate RAG retrieval and answers with deterministic heuristics.

Usage:
  rag_evaluation_harness.py test-set.json pipeline-output.json \
    [--min-context-recall 0.7 --min-faithfulness 0.8]

The test set is an array of query/expected_context/expected_answer objects.
Pipeline output is an array containing retrieved_context (or context) and answer,
aligned by ``id`` when present or otherwise by list position.
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[\w'-]+", re.UNICODE)


def load_array(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{path} must contain an array of objects")
    return data


def texts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [
            str(item.get("text", "")) if isinstance(item, dict) else str(item)
            for item in value
        ]
    if isinstance(value, dict):
        return [str(value.get("text", ""))]
    return []


def tokens(value: Any) -> set[str]:
    return {token.lower() for text in texts(value) for token in TOKEN_RE.findall(text)}


def overlap_metrics(expected: Any, retrieved: Any) -> tuple[float, float]:
    expected_tokens, retrieved_tokens = tokens(expected), tokens(retrieved)
    overlap = len(expected_tokens & retrieved_tokens)
    recall = overlap / len(expected_tokens) if expected_tokens else 1.0
    precision = (
        overlap / len(retrieved_tokens)
        if retrieved_tokens
        else (1.0 if not expected_tokens else 0.0)
    )
    return recall, precision


def normalize(text: str) -> str:
    return " ".join(TOKEN_RE.findall(text.lower()))


def faithfulness(answer: str, context: Any) -> float:
    claims = [
        normalize(part)
        for part in re.split(r"(?<=[.!?])\s+|\n+", answer)
        if normalize(part)
    ]
    normalized_context = normalize(" ".join(texts(context)))
    if not claims:
        return 1.0
    supported = sum(claim in normalized_context for claim in claims)
    return supported / len(claims)


def answer_match(expected: str, actual: str) -> float:
    expected_norm, actual_norm = normalize(expected), normalize(actual)
    if not expected_norm:
        return 1.0
    if expected_norm in actual_norm or actual_norm in expected_norm:
        return 1.0
    expected_tokens, actual_tokens = (
        set(expected_norm.split()),
        set(actual_norm.split()),
    )
    return len(expected_tokens & actual_tokens) / len(expected_tokens)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("test_set", type=Path)
    parser.add_argument("pipeline_output", type=Path)
    parser.add_argument("--min-context-recall", type=float, default=0.0)
    parser.add_argument("--min-context-precision", type=float, default=0.0)
    parser.add_argument("--min-faithfulness", type=float, default=0.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    thresholds = (
        args.min_context_recall,
        args.min_context_precision,
        args.min_faithfulness,
    )
    if any(not 0 <= value <= 1 for value in thresholds):
        parser.error("metric thresholds must be between 0 and 1")
    try:
        tests, outputs = load_array(args.test_set), load_array(args.pipeline_output)
        by_id = {str(item["id"]): item for item in outputs if "id" in item}
        cases = []
        for index, test in enumerate(tests):
            missing = [
                field
                for field in ("query", "expected_context", "expected_answer")
                if field not in test
            ]
            if missing:
                raise ValueError(
                    f"test case {index} missing fields: {', '.join(missing)}"
                )
            output = (
                by_id.get(str(test.get("id")))
                if "id" in test
                else (outputs[index] if index < len(outputs) else None)
            )
            if output is None:
                raise ValueError(f"no pipeline output for test case {index}")
            retrieved = output.get("retrieved_context", output.get("context", []))
            actual_answer = str(output.get("answer", ""))
            recall, precision = overlap_metrics(test["expected_context"], retrieved)
            cases.append(
                {
                    "id": test.get("id", index),
                    "query": test["query"],
                    "context_recall": recall,
                    "context_precision": precision,
                    "answer_faithfulness": faithfulness(actual_answer, retrieved),
                    "answer_expected_match": answer_match(
                        str(test["expected_answer"]), actual_answer
                    ),
                }
            )
        if not cases:
            raise ValueError("test set is empty")
        aggregate = {
            metric: statistics.fmean(case[metric] for case in cases)
            for metric in (
                "context_recall",
                "context_precision",
                "answer_faithfulness",
                "answer_expected_match",
            )
        }
        gates = {
            "context_recall": aggregate["context_recall"] >= args.min_context_recall,
            "context_precision": aggregate["context_precision"]
            >= args.min_context_precision,
            "answer_faithfulness": aggregate["answer_faithfulness"]
            >= args.min_faithfulness,
        }
        report = {
            "passed": all(gates.values()),
            "test_cases": len(cases),
            "aggregate": aggregate,
            "thresholds": {
                "context_recall": args.min_context_recall,
                "context_precision": args.min_context_precision,
                "answer_faithfulness": args.min_faithfulness,
            },
            "gates": gates,
            "cases": cases,
            "methodology": "Token-set overlap for context metrics; normalized claim substring matching for faithfulness.",
        }
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        try:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot write report: {exc}", file=sys.stderr)
            return 2
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
