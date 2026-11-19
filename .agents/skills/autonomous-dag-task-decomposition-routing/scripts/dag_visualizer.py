#!./.venv/bin/python
"""Render a JSON/YAML task DAG as ASCII or Mermaid.

Usage: python dag_visualizer.py dag.json --format mermaid --output dag.md
Critical-path nodes are labeled with `CRITICAL`; no Mermaid styling directives are emitted.
"""

import argparse
import json
import re
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


def graph(data):
    raw = data.get("tasks", data.get("nodes", [])) if isinstance(data, dict) else data
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("input must contain a non-empty tasks list")
    tasks = {}
    for item in raw:
        if not isinstance(item, dict) or not item.get("id"):
            raise RuntimeError("every task needs an id")
        tid = str(item["id"])
        tasks[tid] = {
            "title": str(item.get("title", tid)),
            "deps": [str(x) for x in item.get("dependencies", item.get("deps", []))],
            "weight": float(item.get("duration", item.get("complexity", 1))),
        }
    children, degree = defaultdict(list), {x: 0 for x in tasks}
    for tid, task in tasks.items():
        for dep in task["deps"]:
            if dep not in tasks:
                raise RuntimeError(f"{tid} references missing dependency {dep}")
            children[dep].append(tid)
            degree[tid] += 1
    ready = deque(sorted(x for x, n in degree.items() if n == 0))
    order, waves = [], []
    while ready:
        wave = list(ready)
        ready.clear()
        waves.append(wave)
        for tid in wave:
            order.append(tid)
            for child in children[tid]:
                degree[child] -= 1
                if degree[child] == 0:
                    ready.append(child)
    if len(order) != len(tasks):
        raise RuntimeError("DAG contains a cycle")
    distance, paths = {}, {}
    for tid in order:
        parent = max(tasks[tid]["deps"], key=lambda x: distance[x], default=None)
        distance[tid] = tasks[tid]["weight"] + (distance[parent] if parent else 0)
        paths[tid] = (paths[parent] if parent else []) + [tid]
    end = max(distance, key=distance.get)
    critical = set(paths[end])
    return tasks, waves, critical


def ascii_art(tasks, waves, critical):
    lines = []
    for index, wave in enumerate(waves, 1):
        cells = [
            f"{'*' if tid in critical else ' '}[{tid}] {tasks[tid]['title']}"
            for tid in wave
        ]
        lines.append(f"Wave {index}: " + "  ||  ".join(cells))
        if index < len(waves):
            lines.append(" " * 8 + "↓ dependencies satisfied")
    lines.append("\n* critical path")
    return "\n".join(lines)


def mermaid(tasks, critical):
    def mid(value):
        return "N_" + re.sub(r"\W+", "_", value)

    lines = ["```mermaid", "graph TB"]
    for tid, task in tasks.items():
        label = (
            f"CRITICAL: {tid} — {task['title']}"
            if tid in critical
            else f"{tid} — {task['title']}"
        )
        lines.append(f'    {mid(tid)}["{label.replace(chr(34), chr(39))}"]')
    for tid, task in tasks.items():
        for dep in task["deps"]:
            lines.append(f"    {mid(dep)} --> {mid(tid)}")
    return "\n".join(lines + ["```"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dag", type=Path)
    p.add_argument("--format", choices=("ascii", "mermaid"), default="ascii")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    try:
        tasks, waves, critical = graph(load(a.dag))
        output = (
            ascii_art(tasks, waves, critical)
            if a.format == "ascii"
            else mermaid(tasks, critical)
        )
        if a.output:
            a.output.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
    except (RuntimeError, OSError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
