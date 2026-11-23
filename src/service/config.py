from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_ORIGINS = (
    "http://localhost:8000",
    "http://localhost:5173",
    "http://localhost:3000",
)


def _int_env(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class WhatsAppSettings:
    waba_id: str
    phone_number_id: str
    app_secret: str = field(repr=False)
    verify_token: str = field(repr=False)
    access_token: str = field(repr=False)
    graph_version: str
    allowed_senders: frozenset[str] = field(repr=False)
    db_path: Path
    analysis_mode: str = "rules"


def _whatsapp_settings() -> WhatsAppSettings | None:
    enabled = os.getenv("WHATSAPP_ENABLED", "false").strip().lower()
    if enabled == "false":
        return None
    if enabled != "true":
        raise ValueError("WHATSAPP_ENABLED must be true or false")

    def required(name: str, pattern: str | None = None) -> str:
        value = os.getenv(name, "").strip()
        if not value or (pattern and not re.fullmatch(pattern, value)):
            raise ValueError(f"Missing or invalid {name}")
        return value

    waba_id = required("WHATSAPP_WABA_ID", r"[0-9]{1,32}")
    phone_number_id = required("WHATSAPP_PHONE_NUMBER_ID", r"[0-9]{1,32}")
    app_secret = required("WHATSAPP_APP_SECRET", r"[^\s]{16,256}")
    verify_token = required("WHATSAPP_VERIFY_TOKEN", r"[^\s]{16,256}")
    access_token = required("WHATSAPP_ACCESS_TOKEN", r"[^\s]{1,4096}")
    graph_version = required("WHATSAPP_GRAPH_VERSION", r"v[0-9]{2,3}\.0")
    allowed_senders = frozenset(required("WHATSAPP_ALLOWED_SENDERS").split(","))
    allowed_senders = frozenset(number.strip() for number in allowed_senders)
    if not all(re.fullmatch(r"[1-9][0-9]{6,14}", number) for number in allowed_senders):
        raise ValueError("WHATSAPP_ALLOWED_SENDERS requires international digits-only numbers")
    db_path = Path(required("WHATSAPP_DB_PATH"))
    if not db_path.is_absolute():
        raise ValueError("WHATSAPP_DB_PATH must be an absolute persistent file path")
    analysis_mode = os.getenv("WHATSAPP_ANALYSIS_MODE", "rules").strip()
    if analysis_mode not in {"rules", "auto"}:
        raise ValueError("WHATSAPP_ANALYSIS_MODE must be rules or auto")
    return WhatsAppSettings(
        waba_id=waba_id, phone_number_id=phone_number_id,
        app_secret=app_secret, verify_token=verify_token, access_token=access_token,
        graph_version=graph_version, allowed_senders=allowed_senders,
        db_path=db_path, analysis_mode=analysis_mode,
    )


@dataclass(frozen=True)
class Settings:
    service_name: str = "no-scam"
    version: str = "0.1.0"
    port: int = 8000
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    ai_timeout_ms: int = 8000
    allow_origins: tuple[str, ...] = DEFAULT_ORIGINS
    whatsapp: WhatsAppSettings | None = None

    @property
    def ai_enabled(self) -> bool:
        return bool(self.dashscope_api_key and self.dashscope_base_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = tuple(
        origin.strip()
        for origin in os.getenv("ALLOW_ORIGINS", ",".join(DEFAULT_ORIGINS)).split(",")
        if origin.strip()
    )
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if api_key:
        base_url = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        ).strip()
        model = os.getenv("QWEN_MODEL", "").strip() or "qwen-plus"
        timeout_ms = 8000
    else:
        api_key = os.getenv("QODER_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        host = os.getenv("QODER_HOST", "").strip()
        endpoint = os.getenv("OPENAI_ENDPOINT", "").strip()
        if not base_url and host:
            if not host.startswith(("https://", "http://")):
                host = f"https://{host}"
            base_url = host.rstrip("/") + (f"/{endpoint.lstrip('/')}" if endpoint else "")
        model = os.getenv("WATCHDOG_MODEL", "").strip() or "qwen3.8-flash"
        timeout_ms = 30000

    return Settings(
        port=_int_env("PORT", 8000, minimum=1, maximum=65535),
        dashscope_api_key=api_key,
        dashscope_base_url=base_url.rstrip("/"),
        qwen_model=model,
        ai_timeout_ms=_int_env("AI_TIMEOUT_MS", timeout_ms, minimum=1000, maximum=30000),
        allow_origins=origins or DEFAULT_ORIGINS,
        whatsapp=_whatsapp_settings(),
    )
