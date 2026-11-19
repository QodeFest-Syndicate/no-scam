#!./.venv/bin/python
"""Generate a production-oriented FaaS handler scaffold.

Usage:
  handler_scaffold.py --runtime python --trigger queue --name invoice_worker
  handler_scaffold.py --runtime node --trigger http --name status-api --output src/handler.ts

Generated handlers include idempotency-key extraction, structured logging, and
an error boundary. Replace the in-memory demonstration ledger in production.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTENSIONS = {"python": ".py", "node": ".ts", "go": ".go"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--runtime", required=True, choices=EXTENSIONS)
    parser.add_argument(
        "--trigger", required=True, choices=("http", "queue", "schedule", "event")
    )
    parser.add_argument("--name", required=True, help="Handler/function name")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path; defaults to NAME plus runtime extension",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing output file"
    )
    return parser.parse_args()


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
    if not cleaned or cleaned[0].isdigit():
        raise ValueError("--name must contain letters and may not begin with a digit")
    return cleaned


def python_template(name: str, trigger: str) -> str:
    return f'''#!./.venv/bin/python
"""Generated {trigger} handler for {name}; replace the demo ledger in production."""

import json
import logging
from typing import Any

LOGGER = logging.getLogger("{name}")
LOGGER.setLevel(logging.INFO)
_PROCESSED: dict[str, dict[str, Any]] = {{}}  # Demonstration only; use a durable atomic store.


def _idempotency_key(event: dict[str, Any]) -> str:
    headers = {{str(k).lower(): str(v) for k, v in event.get("headers", {{}}).items()}}
    key = headers.get("idempotency-key") or event.get("id") or event.get("messageId")
    if not key:
        raise ValueError("missing idempotency key/event id")
    return str(key)


def _process(event: dict[str, Any]) -> dict[str, Any]:
    """Implement deterministic domain behavior here."""
    return {{"accepted": True, "trigger": "{trigger}"}}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_id = getattr(context, "aws_request_id", None) or event.get("requestContext", {{}}).get("requestId")
    try:
        key = _idempotency_key(event)
        if key in _PROCESSED:
            LOGGER.info(json.dumps({{"event": "duplicate", "key": key, "request_id": request_id}}))
            return _PROCESSED[key]
        result = _process(event)
        _PROCESSED[key] = result
        LOGGER.info(json.dumps({{"event": "completed", "key": key, "request_id": request_id}}))
        return result
    except ValueError as exc:
        LOGGER.warning(json.dumps({{"event": "rejected", "error": str(exc), "request_id": request_id}}))
        return {{"statusCode": 400, "body": json.dumps({{"error": str(exc)}})}}
    except Exception:
        LOGGER.exception(json.dumps({{"event": "failed", "request_id": request_id}}))
        raise
'''


def node_template(name: str, trigger: str) -> str:
    return f'''/** Generated {trigger} handler for {name}; use a durable ledger in production. */
type Event = {{ id?: string; messageId?: string; headers?: Record<string, string>; [key: string]: unknown }};
type Result = {{ accepted: boolean; trigger: string }};
const processed = new Map<string, Result>(); // Demonstration only.

function idempotencyKey(event: Event): string {{
  const headers = Object.fromEntries(Object.entries(event.headers ?? {{}}).map(([k, v]) => [k.toLowerCase(), v]));
  const key = headers["idempotency-key"] ?? event.id ?? event.messageId;
  if (!key) throw new Error("missing idempotency key/event id");
  return key;
}}

export async function handler(event: Event): Promise<Result> {{
  const key = idempotencyKey(event);
  try {{
    const prior = processed.get(key);
    if (prior) {{ console.info(JSON.stringify({{ event: "duplicate", key }})); return prior; }}
    const result = {{ accepted: true, trigger: "{trigger}" }};
    processed.set(key, result);
    console.info(JSON.stringify({{ event: "completed", key }}));
    return result;
  }} catch (error) {{
    console.error(JSON.stringify({{ event: "failed", key, error: error instanceof Error ? error.message : String(error) }}));
    throw error;
  }}
}}
'''


def go_template(name: str, trigger: str) -> str:
    exported = name[:1].upper() + name[1:]
    return f'''// Generated {trigger} handler for {name}; replace the demo ledger in production.
package handler

import (
    "context"
    "encoding/json"
    "errors"
    "log"
    "sync"
)

type Event struct {{ ID string `json:"id"`; MessageID string `json:"messageId"`; IdempotencyKey string `json:"idempotencyKey"` }}
type Result struct {{ Accepted bool `json:"accepted"`; Trigger string `json:"trigger"` }}
var ledger = struct {{ sync.Mutex; values map[string]Result }}{{values: make(map[string]Result)}}

func {exported}(ctx context.Context, event Event) (result Result, err error) {{
    key := event.IdempotencyKey
    if key == "" {{ key = event.ID }}
    if key == "" {{ key = event.MessageID }}
    if key == "" {{ return Result{{}}, errors.New("missing idempotency key/event id") }}
    defer func() {{
        fields, _ := json.Marshal(map[string]any{{"event": "completed", "key": key, "error": err != nil}})
        log.Print(string(fields))
    }}()
    ledger.Lock()
    defer ledger.Unlock()
    if prior, ok := ledger.values[key]; ok {{ return prior, nil }}
    result = Result{{Accepted: true, Trigger: "{trigger}"}}
    ledger.values[key] = result
    return result, nil
}}
'''


def main() -> int:
    args = parse_args()
    try:
        name = safe_name(args.name)
        output = args.output or Path(name + EXTENSIONS[args.runtime])
        if output.exists() and not args.force:
            raise ValueError(f"output exists: {output}; pass --force to overwrite")
        templates = {
            "python": python_template,
            "node": node_template,
            "go": go_template,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(templates[args.runtime](name, args.trigger), encoding="utf-8")
        if args.runtime == "python":
            output.chmod(output.stat().st_mode | 0o111)
        print(output)
        return 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
