#!./.venv/bin/python
"""Benchmark embedding generation or a deterministic simulated workload.

Usage:
  embedding_benchmark.py corpus.txt --model all-MiniLM-L6-v2 \
    [--mode auto|actual|simulated] [--baseline baseline.json]

The corpus contains one document per line. Actual mode uses sentence-transformers
when installed. Simulated mode measures UTF-8 I/O, tokenization, hashing, and
vector materialization so benchmark plumbing works without a model runtime.
"""

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100.0
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - position) + ordered[high] * (position - low)


def load_corpus(path: Path, limit: int | None) -> tuple[list[str], float]:
    started = time.perf_counter()
    try:
        documents = [
            line.rstrip("\n") for line in path.open(encoding="utf-8") if line.strip()
        ]
    except OSError as exc:
        raise ValueError(f"cannot read corpus: {exc}") from exc
    if limit:
        documents = documents[:limit]
    if not documents:
        raise ValueError("corpus contains no non-empty documents")
    return documents, (time.perf_counter() - started) * 1000.0


def simulated_encoder(dimension: int) -> Callable[[list[str]], list[list[float]]]:
    def encode(batch: list[str]) -> list[list[float]]:
        output = []
        for document in batch:
            tokens = document.lower().split()
            seed = hashlib.sha256(("\x1f".join(tokens)).encode("utf-8")).digest()
            output.append(
                [((seed[i % len(seed)] / 255.0) * 2.0 - 1.0) for i in range(dimension)]
            )
        return output

    return encode


def actual_encoder(
    model_name: str,
) -> tuple[Callable[[list[str]], list[list[float]]], int]:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:
        raise ValueError("sentence-transformers is not installed") from exc
    try:
        model = SentenceTransformer(model_name)
    except Exception as exc:
        raise ValueError(f"cannot load model {model_name}: {exc}") from exc

    def encode(batch: list[str]) -> list[list[float]]:
        vectors = model.encode(batch, show_progress_bar=False)
        return vectors.tolist() if hasattr(vectors, "tolist") else list(vectors)

    dimension = int(model.get_sentence_embedding_dimension())
    return encode, dimension


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "corpus", type=Path, help="UTF-8 file with one document per line"
    )
    parser.add_argument("--model", required=True, help="embedding model name or label")
    parser.add_argument(
        "--mode", choices=("auto", "actual", "simulated"), default="auto"
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--dimension", type=int, default=384, help="simulated vector dimension"
    )
    parser.add_argument("--limit", type=int, help="maximum documents to benchmark")
    parser.add_argument("--baseline", type=Path, help="previous JSON report")
    parser.add_argument("--output", type=Path, help="write JSON report to this path")
    args = parser.parse_args()
    if (
        args.batch_size <= 0
        or args.dimension <= 0
        or (args.limit is not None and args.limit <= 0)
    ):
        parser.error("batch size, dimension, and limit must be positive")
    try:
        documents, io_ms = load_corpus(args.corpus, args.limit)
        mode, fallback_reason = args.mode, None
        if mode != "simulated":
            try:
                encoder, dimension = actual_encoder(args.model)
                mode = "actual"
            except ValueError as exc:
                if args.mode == "actual":
                    raise
                mode, fallback_reason = "simulated", str(exc)
        if mode == "simulated":
            encoder, dimension = simulated_encoder(args.dimension), args.dimension
        latencies: list[float] = []
        encoded = 0
        started = time.perf_counter()
        for offset in range(0, len(documents), args.batch_size):
            batch = documents[offset : offset + args.batch_size]
            batch_started = time.perf_counter()
            vectors = encoder(batch)
            elapsed_ms = (time.perf_counter() - batch_started) * 1000.0
            if len(vectors) != len(batch) or any(
                len(vector) != dimension for vector in vectors
            ):
                raise ValueError(
                    "encoder returned unexpected vector count or dimension"
                )
            latencies.extend([elapsed_ms / len(batch)] * len(batch))
            encoded += len(batch)
        total_seconds = time.perf_counter() - started
        report = {
            "model": args.model,
            "mode": mode,
            "fallback_reason": fallback_reason,
            "documents": encoded,
            "dimension": dimension,
            "batch_size": args.batch_size,
            "io_latency_ms": io_ms,
            "total_seconds": total_seconds,
            "throughput_docs_per_second": encoded / total_seconds,
            "latency_ms": {
                "p50": percentile(latencies, 50),
                "p95": percentile(latencies, 95),
                "p99": percentile(latencies, 99),
                "mean": statistics.fmean(latencies),
            },
        }
        if args.baseline:
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
            base_rate = float(baseline["throughput_docs_per_second"])
            base_p95 = float(baseline["latency_ms"]["p95"])
            report["baseline_comparison"] = {
                "throughput_change_percent": (
                    report["throughput_docs_per_second"] / base_rate - 1
                )
                * 100
                if base_rate
                else None,
                "p95_latency_change_percent": (
                    report["latency_ms"]["p95"] / base_p95 - 1
                )
                * 100
                if base_p95
                else None,
                "dimension_match": baseline.get("dimension") == dimension,
            }
    except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
