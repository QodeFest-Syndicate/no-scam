#!/usr/bin/env bash
# Render boundary_classifier.py or domain_inventory.py JSON as an ASCII diagram.
# Usage: boundary_visualizer.sh [report.json]
# If no file is supplied, JSON is read from stdin.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: boundary_visualizer.sh [REPORT.json]
Render a classifier or inventory gap report. Reads stdin when REPORT is omitted.
EOF
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi
if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi
if [[ $# -eq 1 && ! -r $1 ]]; then
  printf 'error: cannot read %s\n' "$1" >&2
  exit 2
fi

PY_CODE=$(cat <<'PY'
"""Small embedded renderer; accepts a filename argument or JSON on stdin."""
import json
import sys

try:
    if len(sys.argv) > 1 and sys.argv[1]:
        with open(sys.argv[1], encoding="utf-8") as handle:
            report = json.load(handle)
    else:
        report = json.load(sys.stdin)
except (OSError, json.JSONDecodeError) as exc:
    print(f"error: invalid JSON input: {exc}", file=sys.stderr)
    raise SystemExit(2)

print("+" + "-" * 62 + "+")
if "classification" in report:
    model = str(report.get("classification", "unknown")).upper()
    print(f"| DELIVERY BOUNDARY: {model:<43}|")
    print("+" + "-" * 62 + "+")
    for name, detail in report.get("dimensions", {}).items():
        value = detail.get("value")
        state = "YES" if value is True else "NO" if value is False else "UNKNOWN"
        print(f"| {name.replace('_', ' ').title():<24} -> {state:<32}|")
    print("+" + "-" * 62 + "+")
    print("                         |")
    print("                         v")
    print(f"              [ {model} capability boundary ]")
elif "checks" in report:
    status = "COMPLETE" if report.get("complete") else "GAPS FOUND"
    print(f"| DOMAIN INVENTORY: {status:<45}|")
    print("+" + "-" * 62 + "+")
    for name, detail in report.get("checks", {}).items():
        marker = "OK" if detail.get("complete") else "GAP"
        print(f"| [{marker:^3}] {name.replace('_', ' ').title():<54}|")
    print("+" + "-" * 62 + "+")
    for gap in report.get("gaps", []):
        print(f"  ! {gap}")
    domain_map = report.get("domain_map", {})
    for context in domain_map.get("contexts", []):
        print(f"  [Context: {context.get('name')}] --owned by--> [{context.get('owner')}]")
    for asset in domain_map.get("data_ownership", []):
        consumers = asset.get("consumers") or []
        destination = ", ".join(map(str, consumers)) if consumers else "no declared consumers"
        print(f"  [Owner: {asset.get('owner')}] --owns--> [{asset.get('asset')}] --serves--> [{destination}]")
else:
    print("error: unrecognized report shape", file=sys.stderr)
    raise SystemExit(2)
PY
)
python -c "$PY_CODE" "${1:-}"
