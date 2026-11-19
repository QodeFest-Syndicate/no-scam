"""Environment and LLM endpoint resolution.

The Qoder workspace exposes an OpenAI-compatible gateway. We derive the base URL
from ``QODER_HOST`` + ``OPENAI_ENDPOINT`` so the same ``.env`` works for the
swarm, the CLI, and any future ``service`` process.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# src/ai/config.py -> src -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]

# qwen3.8-flash keeps a full swarm pass inside ~20s; override with WATCHDOG_MODEL.
DEFAULT_MODEL = "qwen3.8-flash"
OFFLINE_MODES = {"offline", "off", "rules", "false", "0", "none"}

_loaded = False


def _load_env() -> None:
    """Load ``.env`` once, preferring the working directory over the repo root."""
    global _loaded
    if _loaded:
        return
    for candidate in (Path.cwd() / ".env", _REPO_ROOT / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            break
    _loaded = True


@dataclass(frozen=True)
class LLMSettings:
    model: str
    base_url: str
    api_key: str
    timeout: float


def resolve_settings(mode: str = "auto") -> LLMSettings | None:
    """Return LLM settings, or ``None`` when the caller asked for rules-only mode.

    Returning ``None`` is never an error: every node has a deterministic path so
    the demo keeps working with no network, no credits, or a dead gateway.
    """
    _load_env()
    requested = (mode or os.getenv("WATCHDOG_LLM", "auto")).strip().lower()
    if requested in OFFLINE_MODES or os.getenv("WATCHDOG_LLM", "").strip().lower() in OFFLINE_MODES:
        return None

    host = os.getenv("QODER_HOST", "").strip()
    endpoint = os.getenv("OPENAI_ENDPOINT", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if not base_url and host:
        if not host.startswith("http"):
            host = f"https://{host}"
        base_url = host + endpoint
    api_key = os.getenv("QODER_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    if not base_url or not api_key:
        return None

    timeout = float(os.getenv("WATCHDOG_LLM_TIMEOUT", "45"))
    return LLMSettings(
        model=os.getenv("WATCHDOG_MODEL", DEFAULT_MODEL),
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        timeout=timeout,
    )
