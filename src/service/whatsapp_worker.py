from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Callable

import httpx

from src.service.config import WhatsAppSettings
from src.service.domain import rules
from src.service.domain.types import Assessment, MessageIn
from src.service.whatsapp_store import Job, WhatsAppStore

logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 64 * 1024


@dataclass(frozen=True)
class Delivery:
    state: str
    reason: str
    retry_after: float = 0


def format_reply(assessment: Assessment, mode: str) -> str:
    titles = [
        rules.canonical_signal(signal_id).title
        for signal_id in rules.SIGNAL_ORDER
        if any(signal.id == signal_id for signal in assessment.signals)
    ]
    if titles:
        result = "Reasons to pause:\n" + "\n".join(f"- {title}" for title in titles)
    else:
        result = "No common warning signs found. This does not mean the message is safe."
    engine = "Qwen + local rules" if assessment.engine == "qwen" else (
        "local rules (AI unavailable)" if mode == "auto" else "local rules"
    )
    return (
        f"WatchDog text check\n\n{result}\n\nAnalysis: {engine}.\n\n"
        "Pause before paying, sharing codes or opening links. Verify the request through a contact "
        "or official channel you already know, not details in the forwarded message.\n\n"
        "Warning signs are not proof of a scam. We have not verified the original sender, "
        "opened links or contacted anyone."
    )


def _retry_after(value: str | None, now: float) -> float:
    if value is None:
        return 0
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = parsedate_to_datetime(value).timestamp() - now
        except (ValueError, TypeError, OverflowError):
            return 0
    return max(0, min(seconds, 3600))


class WhatsAppWorker:
    def __init__(
        self, settings: WhatsAppSettings, store: WhatsAppStore,
        assess: Callable[[MessageIn, str], Assessment],
        client: httpx.Client | None = None, clock: Callable[[], float] = time.time,
    ):
        self.settings = settings
        self.store = store
        self.assess = assess
        self.clock = clock
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(10, connect=5, pool=5),
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
            follow_redirects=False, trust_env=False,
        )
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    def close(self) -> None:
        self.client.close()

    def _reply(self, job: Job) -> str:
        if job.reply is not None:
            return job.reply
        if job.kind == "too_long":
            return (
                "WatchDog has not analyzed this message: it exceeds 2,000 characters. "
                "Send a shorter excerpt. Each excerpt is assessed separately and may omit important context."
            )
        if job.kind != "text":
            return (
                "WatchDog's test number analyzes text only. Forward or paste a nonempty text message "
                "of up to 2,000 characters. Photos, audio, documents and other attachments are not analyzed."
            )
        message = MessageIn(
            sender="Original sender unknown", familiar_contact=False, channel="whatsapp", text=job.text,
        )
        try:
            assessment = self.assess(message, self.settings.analysis_mode)
        except Exception:
            logger.warning("whatsapp_analysis_failed; using local rules")
            assessment = rules.assess_with_rules(message)
        return format_reply(assessment, self.settings.analysis_mode)

    def _send(self, job: Job, reply: str) -> Delivery:
        url = (
            f"https://graph.facebook.com/{self.settings.graph_version}/"
            f"{self.settings.phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp", "recipient_type": "individual",
            "to": job.sender, "type": "text", "context": {"message_id": job.message_id},
            "text": {"preview_url": False, "body": reply},
        }
        started = time.monotonic()
        try:
            with self.client.stream(
                "POST", url, json=payload,
                headers={"Authorization": f"Bearer {self.settings.access_token}"},
            ) as response:
                if response.status_code == 429:
                    return Delivery("retry", "rate_limited", _retry_after(response.headers.get("Retry-After"), self.clock()))
                if response.status_code >= 500:
                    return Delivery("uncertain", "upstream_server_error")
                if not 200 <= response.status_code < 300:
                    return Delivery("failed", "upstream_rejected")
                body = bytearray()
                for chunk in response.iter_bytes():
                    if len(body) + len(chunk) > MAX_RESPONSE_BYTES or time.monotonic() - started > 20:
                        return Delivery("uncertain", "invalid_acknowledgement")
                    body.extend(chunk)
                try:
                    data = json.loads(body)
                    message_id = data["messages"][0]["id"]
                    if not isinstance(message_id, str) or not message_id or "error" in data:
                        return Delivery("uncertain", "invalid_acknowledgement")
                except (ValueError, TypeError, KeyError, IndexError, RecursionError):
                    return Delivery("uncertain", "invalid_acknowledgement")
                return Delivery("sent", "api_accepted")
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
            return Delivery("retry", "connection_failed")
        except httpx.RequestError:
            return Delivery("uncertain", "transport_interrupted")

    def process_one(self) -> bool:
        job = self.store.claim(self.clock())
        if job is None:
            return False
        if job.sender not in self.settings.allowed_senders:
            self.store.finish(job, "failed", "recipient_removed")
            return True
        reply = self._reply(job)
        if not self.store.prepare_send(job, reply, self.clock()):
            return True
        delivery = self._send(job, reply)
        if delivery.state == "retry":
            delay = max(delivery.retry_after, min(300, 2 ** job.attempts) + random.uniform(0, 1))
            self.store.retry(job, self.clock() + delay, delivery.reason)
        else:
            self.store.finish(job, delivery.state, delivery.reason)
        logger.info("whatsapp_reply state=%s reason=%s", delivery.state, delivery.reason)
        return True

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                processed = await asyncio.to_thread(self.process_one)
            except Exception:
                logger.error("whatsapp_worker_failed; durable job retained for recovery")
                processed = False
            if not processed:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=1)
                except TimeoutError:
                    pass
