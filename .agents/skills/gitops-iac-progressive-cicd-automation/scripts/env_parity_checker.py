#!./.venv/bin/python
"""Compare nested JSON/YAML environment configurations and report drift.

Usage: python env_parity_checker.py baseline.yaml candidate.yaml [--allow path.to.key]
Repeat --allow for intentional environment-specific overrides.
"""

import argparse
import json
import sys
from pathlib import Path

MISSING = object()


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
            raise RuntimeError(f"invalid YAML in {path}: {exc}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot parse {path}: {exc}") from exc


def flatten(value, prefix=""):
    out = {}
    if isinstance(value, dict):
        for key, child in value.items():
            out.update(flatten(child, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            out.update(flatten(child, f"{prefix}[{i}]"))
        if not value:
            out[prefix] = []
    else:
        out[prefix] = value
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("candidate", type=Path)
    p.add_argument("--allow", action="append", default=[])
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    try:
        left, right = flatten(load(a.baseline)), flatten(load(a.candidate))
        if not left or not right:
            raise RuntimeError("configuration must be a non-empty object or list")
    except (RuntimeError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    drift = []
    for key in sorted(set(left) | set(right)):
        lv, rv = left.get(key, MISSING), right.get(key, MISSING)
        allowed = any(key == x or key.startswith(x + ".") for x in a.allow)
        if lv is MISSING:
            kind = "extra"
        elif rv is MISSING:
            kind = "missing"
        elif lv != rv:
            kind = "different"
        else:
            continue
        drift.append(
            {
                "path": key,
                "type": kind,
                "baseline": "<missing>" if lv is MISSING else lv,
                "candidate": "<missing>" if rv is MISSING else rv,
                "allowed_override": allowed,
            }
        )
    unexpected = [d for d in drift if not d["allowed_override"]]
    if a.format == "json":
        print(
            json.dumps(
                {"drift": drift, "unexpected_count": len(unexpected)},
                indent=2,
                default=str,
            )
        )
    elif drift:
        for d in drift:
            print(
                f"[{'ALLOWED' if d['allowed_override'] else 'DRIFT'}] {d['path']} {d['type']}: {d['baseline']!r} -> {d['candidate']!r}"
            )
    else:
        print("PASS: configurations are structurally identical.")
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
