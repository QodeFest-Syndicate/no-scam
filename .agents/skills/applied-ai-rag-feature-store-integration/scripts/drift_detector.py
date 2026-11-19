#!./.venv/bin/python
"""Detect drift between baseline and current embedding sets.

Usage:
  drift_detector.py baseline.json current.json [--centroid-threshold 0.08]

Inputs are JSON arrays of equal-dimensional float vectors. Metrics include
pairwise cosine distribution shift, paired-vector similarity, centroid drift,
and effective-rank change. Pure Python is used for portable CI checks.
"""

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


def load_vectors(path: Path) -> list[list[float]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{path} must contain a non-empty array")
    vectors = []
    for index, vector in enumerate(raw):
        if not isinstance(vector, list) or not vector:
            raise ValueError(f"vector {index} in {path} is empty or invalid")
        try:
            converted = [float(value) for value in vector]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"vector {index} in {path} contains non-numeric values"
            ) from exc
        if any(not math.isfinite(value) for value in converted):
            raise ValueError(f"vector {index} in {path} contains non-finite values")
        vectors.append(converted)
    dimensions = {len(vector) for vector in vectors}
    if len(dimensions) != 1:
        raise ValueError(f"vectors in {path} have inconsistent dimensions")
    return vectors


def cosine(a: list[float], b: list[float]) -> float:
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (norm_a * norm_b)


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return (
        ordered[lo]
        if lo == hi
        else ordered[lo] * (hi - position) + ordered[hi] * (position - lo)
    )


def summary(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "stddev": statistics.pstdev(values),
        "p05": percentile(values, 0.05),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
    }


def pairwise(vectors: list[list[float]], max_pairs: int) -> list[float]:
    result = []
    for left in range(len(vectors)):
        for right in range(left + 1, len(vectors)):
            result.append(cosine(vectors[left], vectors[right]))
            if len(result) >= max_pairs:
                return result
    return result or [1.0]


def centroid(vectors: list[list[float]]) -> list[float]:
    return [statistics.fmean(values) for values in zip(*vectors)]


def jacobi_eigenvalues(
    matrix: list[list[float]], tolerance: float = 1e-9, max_iterations: int = 2000
) -> list[float]:
    size = len(matrix)
    work = [row[:] for row in matrix]
    for _ in range(max_iterations):
        p, q, magnitude = 0, 0, 0.0
        for i in range(size):
            for j in range(i + 1, size):
                if abs(work[i][j]) > magnitude:
                    p, q, magnitude = i, j, abs(work[i][j])
        if magnitude < tolerance:
            break
        angle = 0.5 * math.atan2(2.0 * work[p][q], work[q][q] - work[p][p])
        c, s = math.cos(angle), math.sin(angle)
        app, aqq, apq = work[p][p], work[q][q], work[p][q]
        work[p][p] = c * c * app - 2 * s * c * apq + s * s * aqq
        work[q][q] = s * s * app + 2 * s * c * apq + c * c * aqq
        work[p][q] = work[q][p] = 0.0
        for k in range(size):
            if k not in (p, q):
                akp, akq = work[k][p], work[k][q]
                work[k][p] = work[p][k] = c * akp - s * akq
                work[k][q] = work[q][k] = s * akp + c * akq
    return [max(0.0, work[i][i]) for i in range(size)]


def effective_rank(vectors: list[list[float]], sample_limit: int = 40) -> float:
    sample = vectors[:sample_limit]
    center = centroid(sample)
    centered = [
        [value - center[i] for i, value in enumerate(vector)] for vector in sample
    ]
    gram = [[sum(x * y for x, y in zip(a, b)) for b in centered] for a in centered]
    eigenvalues = jacobi_eigenvalues(gram)
    total = sum(eigenvalues)
    if total <= 1e-15:
        return 0.0
    probabilities = [value / total for value in eigenvalues if value > 1e-15]
    return math.exp(-sum(p * math.log(p) for p in probabilities))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--cosine-mean-threshold", type=float, default=0.05)
    parser.add_argument("--centroid-threshold", type=float, default=0.08)
    parser.add_argument("--rank-change-threshold", type=float, default=0.20)
    parser.add_argument("--max-pairs", type=int, default=10000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (
        min(
            args.cosine_mean_threshold,
            args.centroid_threshold,
            args.rank_change_threshold,
        )
        < 0
        or args.max_pairs <= 0
    ):
        parser.error("thresholds must be non-negative and max-pairs must be positive")
    try:
        baseline, current = load_vectors(args.baseline), load_vectors(args.current)
        if len(baseline[0]) != len(current[0]):
            raise ValueError(
                f"dimension changed from {len(baseline[0])} to {len(current[0])}"
            )
        baseline_dist, current_dist = (
            summary(pairwise(baseline, args.max_pairs)),
            summary(pairwise(current, args.max_pairs)),
        )
        cosine_mean_shift = abs(current_dist["mean"] - baseline_dist["mean"])
        centroid_drift = 1.0 - cosine(centroid(baseline), centroid(current))
        base_rank, current_rank = effective_rank(baseline), effective_rank(current)
        rank_change = (
            abs(current_rank - base_rank) / base_rank
            if base_rank
            else (1.0 if current_rank else 0.0)
        )
        paired = [cosine(a, b) for a, b in zip(baseline, current)]
        flags = {
            "cosine_distribution_shift": cosine_mean_shift > args.cosine_mean_threshold,
            "centroid_drift": centroid_drift > args.centroid_threshold,
            "effective_rank_change": rank_change > args.rank_change_threshold,
            "record_count_changed": len(baseline) != len(current),
        }
        report: dict[str, Any] = {
            "drift_detected": any(flags.values()),
            "flags": flags,
            "baseline": {
                "count": len(baseline),
                "dimension": len(baseline[0]),
                "cosine_distribution": baseline_dist,
                "effective_rank": base_rank,
            },
            "current": {
                "count": len(current),
                "dimension": len(current[0]),
                "cosine_distribution": current_dist,
                "effective_rank": current_rank,
            },
            "metrics": {
                "cosine_mean_absolute_shift": cosine_mean_shift,
                "centroid_cosine_distance": centroid_drift,
                "effective_rank_relative_change": rank_change,
                "paired_cosine_similarity": summary(paired),
            },
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
    return 1 if report["drift_detected"] else 0


if __name__ == "__main__":
    sys.exit(main())
