#!./.venv/bin/python
"""Validate a JSON/YAML task DAG and calculate its critical path.

Usage: python dag_validator.py dag.yaml [--format text|json]
Expected shape: {tasks: [{id, dependencies: [], duration: 1}]} (nodes/deps also accepted).
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
            raise ValueError(
                "PyYAML is required for YAML; use JSON or install pyyaml"
            ) from exc
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError(f"invalid YAML in {path}: {exc}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc


def analyze(data):
    raw = data.get("tasks", data.get("nodes", [])) if isinstance(data, dict) else data
    if not isinstance(raw, list) or not raw:
        raise ValueError("DAG must contain a non-empty tasks/nodes list")
    tasks, findings = {}, []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict) or not item.get("id"):
            findings.append({"severity": "error", "message": f"task {index} has no id"})
            continue
        tid = str(item["id"])
        if tid in tasks:
            findings.append(
                {"severity": "error", "message": f"duplicate task id: {tid}"}
            )
        tasks[tid] = {
            "deps": [str(x) for x in item.get("dependencies", item.get("deps", []))],
            "duration": float(item.get("duration", item.get("complexity", 1))),
        }
    children, indegree = defaultdict(list), {tid: 0 for tid in tasks}
    for tid, task in tasks.items():
        for dep in task["deps"]:
            if dep == tid:
                findings.append(
                    {"severity": "error", "message": f"{tid} depends on itself"}
                )
            elif dep not in tasks:
                findings.append(
                    {
                        "severity": "error",
                        "message": f"{tid} references missing dependency {dep}",
                    }
                )
            else:
                children[dep].append(tid)
                indegree[tid] += 1
    queue = deque(sorted(tid for tid, degree in indegree.items() if degree == 0))
    order, waves = [], []
    while queue:
        wave = list(queue)
        waves.append(wave)
        queue.clear()
        for tid in wave:
            order.append(tid)
            for child in children[tid]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
    if len(order) != len(tasks):
        findings.append(
            {
                "severity": "error",
                "message": "cycle detected",
                "nodes": sorted(set(tasks) - set(order)),
            }
        )
    isolated = [
        tid for tid, task in tasks.items() if not task["deps"] and not children[tid]
    ]
    if len(tasks) > 1:
        findings.extend(
            {"severity": "error", "message": f"orphan/isolated task: {tid}"}
            for tid in isolated
        )
    distance, paths = {}, {}
    for tid in order:
        valid_deps = [d for d in tasks[tid]["deps"] if d in distance]
        best = max(valid_deps, key=lambda d: distance[d], default=None)
        distance[tid] = tasks[tid]["duration"] + (distance[best] if best else 0)
        paths[tid] = (paths[best] if best else []) + [tid]
    end = max(distance, key=distance.get) if distance else None
    critical = paths.get(end, [])
    width = max((len(w) for w in waves), default=0)
    return {
        "valid": not any(f["severity"] == "error" for f in findings),
        "findings": findings,
        "topological_order": order,
        "critical_path": critical,
        "critical_path_duration": distance.get(end, 0),
        "parallel_waves": waves,
        "maximum_parallelism": width,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dag", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        result = analyze(load(args.dag))
    except (ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"DAG validation: {'PASS' if result['valid'] else 'FAIL'}")
        for f in result["findings"]:
            print(f"[{f['severity'].upper()}] {f['message']}")
        print(
            f"Critical path ({result['critical_path_duration']:g}): {' -> '.join(result['critical_path']) or 'n/a'}"
        )
        print(
            f"Parallel waves: {len(result['parallel_waves'])}; maximum ready-set width: {result['maximum_parallelism']}"
        )
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
