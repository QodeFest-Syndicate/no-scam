from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

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
class Settings:
    service_name: str = "no-scam"
    version: str = "0.1.0"
    port: int = 8000
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    ai_timeout_ms: int = 8000
    allow_origins: tuple[str, ...] = DEFAULT_ORIGINS

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
    )
