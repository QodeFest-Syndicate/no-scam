from __future__ import annotations

import hashlib
import hmac
import json
import logging
import sqlite3
import time
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from src.service.config import WhatsAppSettings
from src.service.whatsapp_store import IncomingMessage, QueueFull, REPLY_WINDOW, WhatsAppStore

logger = logging.getLogger(__name__)
MAX_BODY_BYTES = 256 * 1024
MAX_MESSAGES = 100
Identifier = Annotated[str, Field(strict=True, min_length=1, max_length=256)]


class MetaModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class TextContent(MetaModel):
    body: str = Field(strict=True, max_length=65536)


class MetaMessage(MetaModel):
    sender: str = Field(alias="from", strict=True, pattern=r"^[1-9][0-9]{6,14}$")
    id: Identifier
    timestamp: str = Field(strict=True, pattern=r"^[0-9]{1,12}$")
    type: str = Field(strict=True, min_length=1, max_length=32)
    text: TextContent | None = None


class Metadata(MetaModel):
    phone_number_id: str = Field(strict=True, pattern=r"^[0-9]{1,32}$")


class MessageValue(MetaModel):
    messaging_product: Literal["whatsapp"]
    metadata: Metadata
    messages: list[MetaMessage] = Field(default_factory=list, max_length=MAX_MESSAGES)


class Change(MetaModel):
    field: str = Field(strict=True, max_length=100)
    value: dict[str, Any]


class Entry(MetaModel):
    id: str = Field(strict=True, pattern=r"^[0-9]{1,32}$")
    changes: list[Change] = Field(max_length=100)


class Envelope(MetaModel):
    object: Literal["whatsapp_business_account"]
    entry: list[Entry] = Field(max_length=100)


def normalize(payload: Any, settings: WhatsAppSettings, now: float) -> list[IncomingMessage]:
    envelope = Envelope.model_validate(payload)
    messages = []
    count = 0
    for entry in envelope.entry:
        if entry.id != settings.waba_id:
            continue
        for change in entry.changes:
            if change.field != "messages":
                continue
            metadata = Metadata.model_validate(change.value.get("metadata"))
            if metadata.phone_number_id != settings.phone_number_id:
                continue
            raw_messages = change.value.get("messages", [])
            if isinstance(raw_messages, list) and len(raw_messages) > MAX_MESSAGES:
                raise HTTPException(status_code=413, detail="Too many messages")
            value = MessageValue.model_validate(change.value)
            count += len(value.messages)
            if count > MAX_MESSAGES:
                raise HTTPException(status_code=413, detail="Too many messages")
            for message in value.messages:
                message_at = int(message.timestamp)
                if message.sender not in settings.allowed_senders:
                    continue
                if message_at <= now - REPLY_WINDOW or message_at > now + 300:
                    continue
                text = None
                kind = "unsupported"
                if message.type == "text":
                    if message.text is None:
                        raise ValueError("Missing text")
                    body = message.text.body
                    kind = "empty" if not body.strip() else "too_long" if len(body) > 2000 else "text"
                    if kind == "text":
                        text = body
                messages.append(IncomingMessage(message.id, message.sender, text, kind, message_at))
    return messages


def create_whatsapp_router(settings: WhatsAppSettings | None, store: WhatsAppStore | None) -> APIRouter:
    router = APIRouter()

    @router.get("/webhooks/whatsapp", include_in_schema=False)
    async def verify(request: Request) -> PlainTextResponse:
        if settings is None:
            raise HTTPException(status_code=404, detail="Not found")
        query = request.query_params
        token = query.get("hub.verify_token", "")
        challenge = query.get("hub.challenge", "")
        if (
            query.get("hub.mode") != "subscribe"
            or not hmac.compare_digest(token.encode(), settings.verify_token.encode())
            or not challenge or len(challenge) > 256
        ):
            raise HTTPException(status_code=403, detail="Verification failed")
        return PlainTextResponse(challenge)

    @router.post("/webhooks/whatsapp", include_in_schema=False)
    async def receive(request: Request) -> dict[str, str]:
        if settings is None or store is None:
            raise HTTPException(status_code=404, detail="Not found")
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            raise HTTPException(status_code=415, detail="JSON required")
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_BODY_BYTES:
                raise HTTPException(status_code=413, detail="Payload too large")
            body.extend(chunk)
        expected = "sha256=" + hmac.new(settings.app_secret.encode(), body, hashlib.sha256).hexdigest()
        signature = request.headers.get("x-hub-signature-256", "")
        if not hmac.compare_digest(signature.encode(), expected.encode()):
            raise HTTPException(status_code=403, detail="Invalid signature")
        try:
            messages = normalize(json.loads(body), settings, time.time())
        except (ValidationError, ValueError, TypeError, RecursionError):
            raise HTTPException(status_code=400, detail="Invalid webhook payload") from None
        if messages:
            try:
                await run_in_threadpool(store.enqueue, messages, time.time())
            except (sqlite3.Error, QueueFull, OSError):
                logger.warning("whatsapp_queue_unavailable")
                raise HTTPException(status_code=503, detail="Queue temporarily unavailable") from None
        return {"status": "accepted"}

    return router
