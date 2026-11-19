#!./.venv/bin/python
"""Analyze corpus lengths and recommend a token chunking configuration.

Usage:
  chunk_analyzer.py corpus.txt [--sizes 256,512,1024,2048] [--overlap 0.15]

Input uses one document per line. Token counts are estimated with a portable
word/punctuation tokenizer; validate final settings with the target model's
actual tokenizer and retrieval evaluation.
"""

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def percentile(values: list[int], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return float(
        ordered[lo]
        if lo == hi
        else ordered[lo] * (hi - position) + ordered[hi] * (position - lo)
    )


def chunks_for(length: int, size: int, overlap_tokens: int) -> int:
    if length <= size:
        return 1
    step = size - overlap_tokens
    return 1 + math.ceil((length - size) / step)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("corpus", type=Path, help="UTF-8 corpus, one document per line")
    parser.add_argument(
        "--sizes",
        default="256,512,1024,2048",
        help="comma-separated candidate token sizes",
    )
    parser.add_argument(
        "--overlap", type=float, default=0.15, help="overlap fraction from 0 to <0.5"
    )
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()
    try:
        sizes = sorted(
            {int(value.strip()) for value in args.sizes.split(",") if value.strip()}
        )
        if not sizes or any(size <= 0 for size in sizes):
            raise ValueError("chunk sizes must be positive integers")
        if not 0 <= args.overlap < 0.5:
            raise ValueError("overlap must be at least 0 and below 0.5")
        documents = [
            line.strip()
            for line in args.corpus.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not documents:
            raise ValueError("corpus contains no non-empty documents")
        lengths = [len(TOKEN_RE.findall(document)) for document in documents]
        candidates = []
        for size in sizes:
            overlap_tokens = round(size * args.overlap)
            counts = [chunks_for(length, size, overlap_tokens) for length in lengths]
            unique = sum(lengths)
            duplicated = sum(max(0, count - 1) * overlap_tokens for count in counts)
            redundancy = duplicated / unique if unique else 0.0
            fitting = sum(length <= size for length in lengths) / len(lengths)
            boundary_coverage = (
                1.0
                if overlap_tokens
                else max(0.0, 1.0 - sum(count - 1 for count in counts) / max(1, unique))
            )
            candidates.append(
                {
                    "chunk_size": size,
                    "overlap_tokens": overlap_tokens,
                    "total_chunks": sum(counts),
                    "mean_chunks_per_document": statistics.fmean(counts),
                    "documents_fitting_one_chunk_percent": fitting * 100.0,
                    "estimated_redundancy_percent": redundancy * 100.0,
                    "boundary_context_coverage_percent": boundary_coverage * 100.0,
                }
            )
        target = percentile(lengths, 0.75)
        viable = [
            item
            for item in candidates
            if item["documents_fitting_one_chunk_percent"] >= 60.0
        ]
        pool = viable or candidates
        recommended = min(
            pool,
            key=lambda item: (
                abs(item["chunk_size"] - target),
                item["estimated_redundancy_percent"],
            ),
        )
        if percentile(lengths, 0.95) > max(sizes):
            rationale = "Long-tail documents exceed all candidates; use semantic boundaries and hierarchical retrieval."
        elif recommended["chunk_size"] <= 512:
            rationale = "Short-to-medium documents favor smaller chunks for retrieval precision."
        else:
            rationale = "Longer documents favor larger chunks to preserve local context and limit fragmentation."
        report = {
            "documents": len(documents),
            "tokenizer": "portable-regex-estimate",
            "length_tokens": {
                "min": min(lengths),
                "mean": statistics.fmean(lengths),
                "p50": percentile(lengths, 0.50),
                "p75": target,
                "p95": percentile(lengths, 0.95),
                "max": max(lengths),
            },
            "overlap_fraction": args.overlap,
            "candidates": candidates,
            "recommendation": {
                "chunk_size": recommended["chunk_size"],
                "overlap_tokens": recommended["overlap_tokens"],
                "rationale": rationale,
                "caveat": "Confirm with recall@k and answer-groundedness evaluation.",
            },
        }
    except (OSError, ValueError) as exc:
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
