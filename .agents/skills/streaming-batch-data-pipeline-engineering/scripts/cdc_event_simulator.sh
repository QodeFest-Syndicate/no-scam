#!/usr/bin/env bash
# Generate synthetic Debezium-style CDC JSON events from a JSON schema.
#
# Usage:
#   cdc_event_simulator.sh --table customers --operation insert --count 10 \
#     --schema-file customer.schema.json [--output events.jsonl]
#
# The schema may be JSON Schema (properties), Avro (fields), or a simple object
# mapping field names to types. Events are written as JSON Lines.

set -euo pipefail

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
}

TABLE=""
OPERATION=""
COUNT=""
SCHEMA_FILE=""
OUTPUT="-"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --table) TABLE="${2:-}"; shift 2 ;;
    --operation) OPERATION="${2:-}"; shift 2 ;;
    --count) COUNT="${2:-}"; shift 2 ;;
    --schema-file) SCHEMA_FILE="${2:-}"; shift 2 ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$TABLE" || -z "$OPERATION" || -z "$COUNT" || -z "$SCHEMA_FILE" ]]; then
  echo "error: --table, --operation, --count, and --schema-file are required" >&2
  usage >&2
  exit 2
fi
if [[ ! "$OPERATION" =~ ^(insert|update|delete)$ ]]; then
  echo "error: --operation must be insert, update, or delete" >&2
  exit 2
fi
if [[ ! "$COUNT" =~ ^[1-9][0-9]*$ ]]; then
  echo "error: --count must be a positive integer" >&2
  exit 2
fi
if [[ ! -r "$SCHEMA_FILE" ]]; then
  echo "error: schema file is not readable: $SCHEMA_FILE" >&2
  exit 2
fi
if ! command -v python >/dev/null 2>&1; then
  echo "error: python is required" >&2
  exit 2
fi

python - "$TABLE" "$OPERATION" "$COUNT" "$SCHEMA_FILE" "$OUTPUT" <<'PY'
import datetime as dt
import json
import random
import sys
from pathlib import Path


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def field_map(schema):
    if isinstance(schema.get("properties"), dict):
        return {name: spec.get("type", "string") if isinstance(spec, dict) else spec
                for name, spec in schema["properties"].items()}
    if isinstance(schema.get("fields"), list):
        return {field["name"]: field.get("type", "string") for field in schema["fields"]
                if isinstance(field, dict) and "name" in field}
    ignored = {"$schema", "title", "description", "type", "required"}
    return {key: value for key, value in schema.items() if key not in ignored}


def value_for(name, raw_type, index):
    if isinstance(raw_type, list):
        raw_type = next((item for item in raw_type if item != "null"), "string")
    if isinstance(raw_type, dict):
        raw_type = raw_type.get("type", "string")
    kind = str(raw_type).lower()
    if name.lower() in ("id", "pk") or name.lower().endswith("_id"):
        return index
    if kind in ("int", "integer", "long", "number", "float", "double"):
        return index * 10
    if kind in ("boolean", "bool"):
        return index % 2 == 0
    if kind in ("array",):
        return []
    if kind in ("object", "record", "map"):
        return {}
    return f"{name}_{index}"


table, operation, count_text, schema_path, output_path = sys.argv[1:]
try:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    fail(f"cannot load schema: {exc}")
if not isinstance(schema, dict):
    fail("schema root must be a JSON object")
fields = field_map(schema)
if not fields:
    fail("schema contains no fields")
count = int(count_text)
op_code = {"insert": "c", "update": "u", "delete": "d"}[operation]
stream = sys.stdout
if output_path != "-":
    try:
        stream = Path(output_path).open("w", encoding="utf-8")
    except OSError as exc:
        fail(f"cannot open output: {exc}")
try:
    base_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    for offset in range(count):
        index = offset + 1
        current = {name: value_for(name, field_type, index) for name, field_type in fields.items()}
        previous = {**current}
        if current:
            mutable = next((key for key in current if key.lower() not in ("id", "pk") and not key.lower().endswith("_id")), None)
            if mutable:
                previous[mutable] = value_for(mutable, fields[mutable], index + 100000)
        before = previous if operation in ("update", "delete") else None
        after = current if operation in ("insert", "update") else None
        event = {
            "schema": {"type": "struct", "name": f"{table}.Envelope"},
            "payload": {
                "before": before,
                "after": after,
                "source": {"connector": "synthetic", "name": "cdc-event-simulator",
                           "table": table, "snapshot": "false", "ts_ms": base_ms + offset},
                "op": op_code,
                "ts_ms": base_ms + offset,
                "transaction": None,
            },
        }
        stream.write(json.dumps(event, separators=(",", ":")) + "\n")
finally:
    if stream is not sys.stdout:
        stream.close()
PY
