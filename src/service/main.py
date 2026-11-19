from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.service.ai import qwen
from src.service.config import get_settings
from src.service.domain import recovery, rules
from src.service.domain.scenarios import SCENARIOS
from src.service.domain.types import (
    AssessRequest,
    AssessResponse,
    Assessment,
    MetaResponse,
    MessageIn,
    RecoveryRequest,
    RecoveryResponse,
    ScenariosResponse,
)

from src.service.whatsapp import create_whatsapp_router
from src.service.whatsapp_store import WhatsAppStore
from src.service.whatsapp_worker import WhatsAppWorker

logger = logging.getLogger(__name__)

_STARTED_AT = time.monotonic()
AssessMode = Literal["auto", "ai", "rules"]


def _assess(message: MessageIn, mode: AssessMode) -> Assessment:
    fallback = rules.assess_with_rules(message)
    if mode == "rules":
        return fallback
    try:
        enriched = qwen.assess_with_qwen(message, fallback)
    except Exception as exc:
        logger.warning("Qwen enrichment failed (%s); serving rules assessment", type(exc).__name__)
        enriched = None
    if enriched is None:
        if mode == "ai":
            raise HTTPException(
                status_code=503,
                detail=(
                    "Qwen is unavailable. Retry with mode=auto for the rules "
                    "assessment."
                ),
            )
        return fallback
    return enriched


def create_app() -> FastAPI:
    settings = get_settings()
    whatsapp = settings.whatsapp
    store = WhatsAppStore(whatsapp.db_path, f"{whatsapp.waba_id}:{whatsapp.phone_number_id}") if whatsapp else None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if whatsapp is None or store is None:
            yield
            return
        await asyncio.to_thread(store.initialize)
        worker = WhatsAppWorker(whatsapp, store, _assess)
        stop = asyncio.Event()
        task = asyncio.create_task(worker.run(stop))
        try:
            yield
        finally:
            stop.set()
            await task
            worker.close()

    app = FastAPI(
        lifespan=lifespan,
        title="WatchDog AI demo backend",
        description=(
            "Reasons to pause, visible evidence and calm next steps for one "
            "scripted scam scenario. Demo data only."
        ),
        version=settings.version,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allow_origins),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "uptime": round(time.monotonic() - _STARTED_AT, 3)}

    @app.get("/api/meta", response_model=MetaResponse)
    def meta() -> MetaResponse:
        return MetaResponse(
            service=settings.service_name,
            engine="qwen" if settings.ai_enabled else "rules",
            ai_enabled=settings.ai_enabled,
            demo_data_only=True,
            version=settings.version,
        )

    @app.get("/api/scenarios", response_model=ScenariosResponse)
    def scenarios() -> ScenariosResponse:
        return ScenariosResponse(scenarios=list(SCENARIOS))

    @app.post("/api/assess", response_model=AssessResponse)
    def assess(request: AssessRequest, mode: AssessMode = "auto") -> AssessResponse:
        return AssessResponse(assessment=_assess(request.message, mode))

    @app.post("/api/recovery", response_model=RecoveryResponse)
    def recovery_guidance(request: RecoveryRequest) -> RecoveryResponse:
        return recovery.get_recovery(request.incident)

    app.include_router(create_whatsapp_router(whatsapp, store))

    ui_dir = Path(__file__).resolve().parents[1] / "ui"
    if (ui_dir / "index.html").is_file():
        app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
    else:

        @app.get("/", include_in_schema=False)
        def index() -> dict[str, str]:
            return {
                "service": settings.service_name,
                "message": "WatchDog AI demo backend. POST /api/assess to assess a message.",
                "docs": "/docs",
            }

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=get_settings().port)
