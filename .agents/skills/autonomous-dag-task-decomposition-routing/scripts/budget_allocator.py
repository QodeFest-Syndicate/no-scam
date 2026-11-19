#!./.venv/bin/python
"""Allocate a numeric time/token budget across DAG tasks.

Usage: python budget_allocator.py dag.json --total-budget 100000 --contingency 0.15
Tasks accept id, dependencies/deps, complexity, and optional risk (1-5).
"""

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path


def load(path):
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            return json.loads(text)
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required for YAML input") from exc
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"invalid YAML: {exc}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot parse input: {exc}") from exc


def allocate(data, total, contingency):
    raw = data.get("tasks", data.get("nodes", [])) if isinstance(data, dict) else data
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("non-empty tasks list required")
    tasks = {}
    for item in raw:
        tid = str(item.get("id", ""))
        if not tid or tid in tasks:
            raise RuntimeError("task IDs must be present and unique")
        complexity = float(item.get("complexity", item.get("duration", 1)))
        risk = float(item.get("risk", 1))
        if complexity <= 0 or risk <= 0:
            raise RuntimeError(f"{tid}: complexity and risk must be positive")
        tasks[tid] = {
            "deps": [str(x) for x in item.get("dependencies", item.get("deps", []))],
            "complexity": complexity,
            "risk": risk,
        }
    children, degree = defaultdict(list), {x: 0 for x in tasks}
    for tid, task in tasks.items():
        for dep in task["deps"]:
            if dep not in tasks:
                raise RuntimeError(f"{tid}: missing dependency {dep}")
            children[dep].append(tid)
            degree[tid] += 1
    q = deque(x for x, n in degree.items() if n == 0)
    order = []
    while q:
        tid = q.popleft()
        order.append(tid)
        for child in children[tid]:
            degree[child] -= 1
            q.append(child) if degree[child] == 0 else None
    if len(order) != len(tasks):
        raise RuntimeError("cycle detected")
    dist, paths = {}, {}
    for tid in order:
        parent = max(tasks[tid]["deps"], key=lambda x: dist[x], default=None)
        dist[tid] = tasks[tid]["complexity"] + (dist[parent] if parent else 0)
        paths[tid] = (paths[parent] if parent else []) + [tid]
    critical = set(paths[max(dist, key=dist.get)])
    reserve = total * contingency
    distributable = total - reserve
    weights = {
        tid: t["complexity"]
        * (1 + 0.15 * (t["risk"] - 1))
        * (1.35 if tid in critical else 1)
        for tid, t in tasks.items()
    }
    weight_sum = sum(weights.values())
    raw_alloc = {tid: distributable * w / weight_sum for tid, w in weights.items()}
    rounded = {tid: int(v) for tid, v in raw_alloc.items()}
    remainder = int(round(distributable - sum(rounded.values())))
    for tid in sorted(tasks, key=lambda x: raw_alloc[x] - rounded[x], reverse=True)[
        : max(0, remainder)
    ]:
        rounded[tid] += 1
    return {
        "total_budget": total,
        "contingency_reserved": reserve,
        "critical_path": [x for x in order if x in critical],
        "allocations": [
            {
                "task": tid,
                "budget": rounded[tid],
                "warning_threshold": round(rounded[tid] * 0.8),
                "critical": tid in critical,
            }
            for tid in order
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dag", type=Path)
    p.add_argument("--total-budget", required=True, type=float)
    p.add_argument("--contingency", type=float, default=0.15)
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    if a.total_budget <= 0 or not 0 <= a.contingency < 1:
        p.error("budget must be positive and contingency in [0,1)")
    try:
        result = allocate(load(a.dag), a.total_budget, a.contingency)
    except (RuntimeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if a.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(
            f"Budget {result['total_budget']:g}; contingency {result['contingency_reserved']:g}; critical path: {' -> '.join(result['critical_path'])}"
        )
        for row in result["allocations"]:
            print(
                f"{row['task']}: {row['budget']} (warn {row['warning_threshold']}){' CRITICAL' if row['critical'] else ''}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
