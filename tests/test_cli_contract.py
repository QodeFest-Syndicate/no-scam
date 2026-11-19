"""Process contract: ``python -m ai`` is what ``service`` can shell out to."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_KEYS = {
    "verdict",
    "confidence",
    "headline",
    "reasons",
    "unknown",
    "recommended_actions",
    "verification_route",
    "checks",
    "choices",
    "companion_hint",
    "guardrail_note",
    "sources",
    "rubric_score",
    "trace",
    "elapsed_ms",
}


def _run(args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "WATCHDOG_LLM": "offline"}
    return subprocess.run(
        [sys.executable, "-m", "ai", *args],
        cwd=ROOT,
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )


def test_demo_prints_a_complete_contract() -> None:
    result = _run(["--demo", "familiar-link", "--mode", "offline"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["verdict"] == "high"
    assert payload["rubric_score"] == 1.0
    assert payload["checks"]
    assert all("source" in check for check in payload["checks"])


def test_stdin_json_round_trip() -> None:
    request = {
        "incident": {
            "channel": "whatsapp",
            "sender_display_name": "Aunty",
            "sender_handle": "+60 12-000 0000",
            "message_text": "Urgent, transfer RM900 now and don't tell anyone.",
            "perimeter": [
                {
                    "name": "Aunty",
                    "known_handles": ["+60 12-000 0000"],
                    "known_channels": ["whatsapp"],
                }
            ],
        }
    }
    result = _run(["--mode", "offline"], stdin=json.dumps(request))
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["verdict"] in {"elevated", "high"}
    assert payload["checks"]


def test_stream_ends_with_the_assessment() -> None:
    result = _run(["--demo", "benign-family-message", "--mode", "offline", "--stream"])
    assert result.returncode == 0, result.stderr
    chunks = [json.loads(line) for line in result.stdout.strip().splitlines()]
    assert chunks, "no stream chunks"
    assert chunks[-1]["done"] is True
    assert chunks[-1]["assessment"]["verdict"] == "low"
    assert {"intake", "finalize"} & {chunk["node"] for chunk in chunks}


def test_list_demos() -> None:
    result = _run(["--list-demos"])
    assert result.returncode == 0, result.stderr
    assert "already-clicked" in result.stdout


def test_health_never_leaks_the_key() -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [sys.executable, "-m", "ai", "--health"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["package"] == "ai"
    assert "api_key" not in result.stdout.lower()
    assert "sk-ws-" not in result.stdout


def test_bad_json_exits_two() -> None:
    result = _run([], stdin="{not json")
    assert result.returncode == 2
    assert "invalid JSON" in result.stderr


def test_missing_incident_exits_two() -> None:
    result = _run([], stdin=json.dumps({"wrong": "shape"}))
    assert result.returncode == 2
    assert "invalid request" in result.stderr
