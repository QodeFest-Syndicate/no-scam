#!./.venv/bin/python
"""Estimate cold-start impact from requirements.txt, package.json, or go.mod.

Usage: cold_start_analyzer.py PATH [--pretty]

The size estimate uses installed package directories when discoverable and a
small conservative heuristic otherwise. Treat estimates as prioritization data,
then measure INIT duration on the target platform.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

HEAVY_MB = {
    "tensorflow": 500,
    "torch": 700,
    "numpy": 35,
    "pandas": 70,
    "scipy": 90,
    "boto3": 25,
    "aws-sdk": 45,
    "playwright": 120,
    "puppeteer": 180,
    "next": 80,
    "@google-cloud/storage": 25,
    "google.golang.org/api": 20,
}
LAZY = {
    "tensorflow",
    "torch",
    "pandas",
    "scipy",
    "playwright",
    "puppeteer",
    "matplotlib",
    "sharp",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("manifest", type=Path, help="Dependency manifest path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser.parse_args()


def directory_size(path: Path) -> int:
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except OSError:
        return 0
    return total


def parse_requirements(text: str) -> list[str]:
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r", "--")):
            continue
        name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip()
        if name:
            result.append(name)
    return result


def parse_package(text: str) -> list[str]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("package.json must be an object")
    return sorted(
        set(data.get("dependencies", {})) | set(data.get("optionalDependencies", {}))
    )


def parse_go_mod(text: str) -> list[str]:
    dependencies: list[str] = []
    in_block = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "require (":
            in_block = True
            continue
        if in_block and line == ")":
            in_block = False
            continue
        if line.startswith("require "):
            parts = line.split()
            if len(parts) >= 2:
                dependencies.append(parts[1])
        elif in_block and line and not line.startswith("//"):
            dependencies.append(line.split()[0])
    return dependencies


def installed_python_size(name: str) -> int:
    spec = importlib.util.find_spec(name.replace("-", "_"))
    if not spec or not spec.origin:
        return 0
    location = Path(spec.origin)
    return (
        directory_size(location.parent)
        if location.name == "__init__.py"
        else location.stat().st_size
    )


def analyze(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if path.name == "requirements.txt" or path.suffix == ".txt":
        runtime, dependencies = "python", parse_requirements(text)
    elif path.name == "package.json":
        runtime, dependencies = "node", parse_package(text)
    elif path.name == "go.mod":
        runtime, dependencies = "go", parse_go_mod(text)
    else:
        raise ValueError(
            "supported manifests are requirements.txt, package.json, and go.mod"
        )

    details = []
    total = 0
    node_modules = path.parent / "node_modules"
    for name in dependencies:
        measured = 0
        if runtime == "python":
            measured = installed_python_size(name)
        elif runtime == "node" and (node_modules / name).exists():
            measured = directory_size(node_modules / name)
        estimate = measured or int(HEAVY_MB.get(name, 1.5) * 1024 * 1024)
        total += estimate
        details.append(
            {
                "name": name,
                "estimated_bytes": estimate,
                "measured": bool(measured),
                "lazy_load_candidate": name in LAZY,
            }
        )

    recommendations = []
    if len(dependencies) > 25:
        recommendations.append(
            "Reduce direct production dependencies and split unrelated handlers."
        )
    if total > 50 * 1024 * 1024:
        recommendations.append(
            "Bundle-prune and measure compressed and uncompressed artifact size."
        )
    if any(item["lazy_load_candidate"] for item in details):
        recommendations.append(
            "Move optional heavy imports behind the branch that needs them."
        )
    if runtime == "node":
        recommendations.append(
            "Bundle with tree-shaking and exclude development dependencies/source maps."
        )
    elif runtime == "python":
        recommendations.append(
            "Prefer targeted imports; remove tests, caches, and unused native wheels."
        )
    else:
        recommendations.append(
            "Use build tags carefully and inspect the stripped binary with go tool nm."
        )
    recommendations.append(
        "Validate priorities with cold INIT duration and memory measurements."
    )
    return {
        "manifest": str(path),
        "runtime": runtime,
        "dependency_count": len(dependencies),
        "estimated_total_bytes": total,
        "estimated_total_mb": round(total / 1024 / 1024, 2),
        "dependencies": details,
        "lazy_loadable_candidates": [
            d["name"] for d in details if d["lazy_load_candidate"]
        ],
        "recommendations": recommendations,
    }


def main() -> int:
    args = parse_args()
    try:
        report = analyze(args.manifest)
        json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
