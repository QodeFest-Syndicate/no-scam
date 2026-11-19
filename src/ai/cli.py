"""Command-line contract used by ``service``.

    python -m ai --demo familiar-link --mode offline     # scripted demo
    python -m ai --demo already-clicked --stream         # NDJSON progress
    python -m ai < request.json > assessment.json        # stdin/stdout contract
    python -m ai --health                                # readiness probe
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from .api import assess_json, health, stream_events
from .fixtures import list_cases, load_case
from .schemas import AssessmentRequest

EXIT_OK = 0
EXIT_BAD_INPUT = 2
EXIT_RUNTIME = 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai",
        description="WatchDog AI swarm: assess one interaction and print an assessment.",
    )
    parser.add_argument("--demo", choices=[name for name, _ in list_cases()], help="run a scripted scenario")
    parser.add_argument("--list-demos", action="store_true", help="list scripted scenarios and exit")
    parser.add_argument("--mode", choices=["auto", "llm", "offline"], default=None)
    parser.add_argument("--stream", action="store_true", help="emit NDJSON progress per node")
    parser.add_argument("--health", action="store_true", help="print readiness information and exit")
    parser.add_argument("--out", type=Path, default=None, help="write output to a file instead of stdout")
    return parser


def _read_payload(args: argparse.Namespace) -> dict | AssessmentRequest:
    if args.demo:
        return load_case(args.demo)
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("no request on stdin; pass --demo NAME or pipe a JSON request")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("request must be a JSON object")
    return payload


def _emit(text: str, out: Path | None) -> None:
    if out is None:
        sys.stdout.write(text + "\n")
        return
    out.write_text(text + "\n", encoding="utf-8")
    sys.stderr.write(f"written: {out}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.health:
        _emit(json.dumps(health(), indent=2), args.out)
        return EXIT_OK

    if args.list_demos:
        lines = [f"{name}\t{title}" for name, title in list_cases()]
        _emit("\n".join(lines), args.out)
        return EXIT_OK

    try:
        payload = _read_payload(args)
        request = payload if isinstance(payload, AssessmentRequest) else AssessmentRequest.model_validate(payload)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"invalid JSON: {exc}\n")
        return EXIT_BAD_INPUT
    except ValidationError as exc:
        sys.stderr.write(f"invalid request: {exc.errors()}\n")
        return EXIT_BAD_INPUT
    except (OSError, ValueError, KeyError) as exc:
        sys.stderr.write(f"bad input: {exc}\n")
        return EXIT_BAD_INPUT

    try:
        if args.stream:
            lines = [
                json.dumps(chunk, ensure_ascii=False)
                for chunk in stream_events(request, mode=args.mode)
            ]
            _emit("\n".join(lines), args.out)
        else:
            result = assess_json(request, mode=args.mode)
            _emit(json.dumps(result, indent=2, ensure_ascii=False), args.out)
    except Exception as exc:  # the swarm should not crash; if it does, stay honest
        sys.stderr.write(f"assessment failed: {type(exc).__name__}: {exc}\n")
        return EXIT_RUNTIME

    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
