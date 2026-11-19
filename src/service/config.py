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
        return bool(self.dashscope_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = tuple(
        origin.strip()
        for origin in os.getenv("ALLOW_ORIGINS", ",".join(DEFAULT_ORIGINS)).split(",")
        if origin.strip()
    )
    return Settings(
        port=_int_env("PORT", 8000, minimum=1, maximum=65535),
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", "").strip(),
        dashscope_base_url=os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        ).strip(),
        qwen_model=os.getenv("QWEN_MODEL", "qwen-plus").strip() or "qwen-plus",
        ai_timeout_ms=_int_env("AI_TIMEOUT_MS", 8000, minimum=1000, maximum=30000),
        allow_origins=origins or DEFAULT_ORIGINS,
    )
