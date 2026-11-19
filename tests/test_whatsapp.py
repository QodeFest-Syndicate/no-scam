import copy
import hashlib
import hmac
import json
import logging
import socket
import sqlite3
import threading
import time
from contextlib import closing
from dataclasses import replace
from unittest.mock import Mock

import httpx
import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.service import config, main, whatsapp
from src.service.config import Settings, WhatsAppSettings
from src.service.domain import rules
from src.service.whatsapp_store import IncomingMessage, REPLY_WINDOW, WhatsAppStore
from src.service.whatsapp_worker import WhatsAppWorker, format_reply

NOW = 1_800_000_000
SENDER = "60123456789"
TEXT = "Pay RM500 urgently at https://fictional.invalid now. Don't call."


@pytest.fixture
def settings(tmp_path):
    return WhatsAppSettings(
        waba_id="12345", phone_number_id="67890", app_secret="fictional-app-secret",
        verify_token="fictional-verify-token", access_token="fictional-access-token",
        graph_version="v23.0", allowed_senders=frozenset({SENDER}),
        db_path=tmp_path / "inbox.sqlite3",
    )


@pytest.fixture
def store(settings):
    result = WhatsAppStore(settings.db_path, f"{settings.waba_id}:{settings.phone_number_id}")
    result.initialize()
    return result


@pytest.fixture
def http(settings, store, monkeypatch):
    monkeypatch.setattr(whatsapp.time, "time", lambda: NOW)
    app = FastAPI()
    app.include_router(whatsapp.create_whatsapp_router(settings, store))
    with TestClient(app) as client:
        yield client


def payload(settings, *, text=TEXT, message_id="wamid.test", sender=SENDER, timestamp=NOW, kind="text"):
    return {
        "object": "whatsapp_business_account",
        "entry": [{"id": settings.waba_id, "changes": [{"field": "messages", "value": {
            "messaging_product": "whatsapp", "metadata": {"phone_number_id": settings.phone_number_id},
            "contacts": [{"profile": {"name": "Forwarder, not original author"}, "wa_id": sender}],
            "messages": [{"from": sender, "id": message_id, "timestamp": str(timestamp),
                          "type": kind, "text": {"body": text}}],
        }}]}],
    }


def value(data):
    return data["entry"][0]["changes"][0]["value"]


def signed(settings, data):
    body = json.dumps(data, ensure_ascii=False).encode()
    signature = hmac.new(settings.app_secret.encode(), body, hashlib.sha256).hexdigest()
    return {"content": body, "headers": {"content-type": "application/json", "x-hub-signature-256": "sha256=" + signature}}


def rows(store):
    with sqlite3.connect(store.path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM jobs ORDER BY rowid")]


def enqueue(store, *, kind="text", text=TEXT, at=NOW, sender=SENDER):
    store.enqueue([IncomingMessage("wamid.test", sender, text, kind, at)], NOW)


@pytest.fixture
def worker_factory(settings, store):
    workers = []

    def make(handler=None, assessor=None, mode="rules", clock=None):
        if handler is None:
            handler = lambda request: httpx.Response(200, json={"messages": [{"id": "wamid.reply"}]})
        worker = WhatsAppWorker(
            replace(settings, analysis_mode=mode), store,
            assessor if assessor is not None else lambda message, mode: rules.assess_with_rules(message),
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            clock=clock or (lambda: NOW),
        )
        workers.append(worker)
        return worker

    yield make
    for worker in workers:
        worker.close()


def test_challenge(http, settings, store):
    response = http.get("/webhooks/whatsapp", params={
        "hub.mode": "subscribe", "hub.verify_token": settings.verify_token, "hub.challenge": "123456",
    })
    assert response.status_code == 200
    assert response.text == "123456"
    assert response.headers["content-type"].startswith("text/plain")
    assert rows(store) == []


@pytest.mark.parametrize("overrides", [
    {"hub.mode": "unsubscribe"}, {"hub.verify_token": "incorrect"},
    {"hub.challenge": ""}, {"hub.challenge": "x" * 257},
])
def test_challenge_denied(http, settings, overrides):
    params = {"hub.mode": "subscribe", "hub.verify_token": settings.verify_token, "hub.challenge": "123"}
    params.update(overrides)
    response = http.get("/webhooks/whatsapp", params=params)
    assert response.status_code == 403
    assert settings.verify_token not in response.text


def test_disabled_route_precedes_ui(monkeypatch):
    monkeypatch.setattr(main, "get_settings", lambda: Settings())
    with TestClient(main.create_app()) as client:
        assert client.get("/webhooks/whatsapp").status_code == 404
        assert client.post("/webhooks/whatsapp", json={}).status_code == 404
        assert client.get("/health").status_code == 200


def test_text_is_committed_before_ack_without_analysis(http, settings, store, monkeypatch):
    assess = Mock(side_effect=AssertionError("must not analyze in webhook"))
    monkeypatch.setattr(main, "_assess", assess)
    data = payload(settings)
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 200
    saved = rows(store)
    assert len(saved) == 1
    assert saved[0]["text"] == TEXT
    assert saved[0]["sender"] == SENDER
    assert saved[0]["state"] == "pending"
    assert "Forwarder" not in str(saved)
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 200
    assert len(rows(store)) == 1
    assess.assert_not_called()


@pytest.mark.parametrize("signature", [None, "sha256=bad", "sha1=123", "fictional-verify-token"])
def test_signature_denied(http, settings, store, signature):
    request = signed(settings, payload(settings))
    if signature is None:
        request["headers"].pop("x-hub-signature-256")
    else:
        request["headers"]["x-hub-signature-256"] = signature
    assert http.post("/webhooks/whatsapp", **request).status_code == 403
    assert rows(store) == []


def test_signature_covers_exact_bytes(http, settings, store):
    request = signed(settings, payload(settings))
    request["content"] += b" "
    assert http.post("/webhooks/whatsapp", **request).status_code == 403
    assert rows(store) == []


@pytest.mark.parametrize("data", [None, [], {}, {"object": "wrong", "entry": []}])
def test_malformed_envelope(http, settings, store, data):
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 400
    assert rows(store) == []


def test_invalid_json_and_media_type_and_size(http, settings, store):
    body = b"{not-json"
    signature = "sha256=" + hmac.new(settings.app_secret.encode(), body, hashlib.sha256).hexdigest()
    headers = {"content-type": "application/json", "x-hub-signature-256": signature}
    assert http.post("/webhooks/whatsapp", content=body, headers=headers).status_code == 400
    assert http.post("/webhooks/whatsapp", content=body).status_code == 415
    assert http.post("/webhooks/whatsapp", content=b"x" * (whatsapp.MAX_BODY_BYTES + 1), headers=headers).status_code == 413
    assert rows(store) == []


@pytest.mark.parametrize("mutation", ["waba", "phone", "field", "sender", "statuses", "stale", "future"])
def test_irrelevant_events_do_not_enqueue(http, settings, store, mutation):
    data = payload(settings)
    if mutation == "waba":
        data["entry"][0]["id"] = "999"
    elif mutation == "phone":
        value(data)["metadata"]["phone_number_id"] = "999"
    elif mutation == "field":
        data["entry"][0]["changes"][0]["field"] = "other_update"
    elif mutation == "sender":
        value(data)["messages"][0]["from"] = "60999999999"
    elif mutation == "statuses":
        value(data).pop("messages")
        value(data)["statuses"] = [{"id": "wamid.outbound", "status": "delivered"}]
    else:
        value(data)["messages"][0]["timestamp"] = str(NOW - REPLY_WINDOW if mutation == "stale" else NOW + 301)
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 200
    assert rows(store) == []


def test_batch_and_atomic_invalid_batch(http, settings, store):
    data = payload(settings)
    second = copy.deepcopy(value(data)["messages"][0])
    second["id"] = "wamid.second"
    second["timestamp"] = "invalid"
    value(data)["messages"].append(second)
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 400
    assert rows(store) == []
    second["timestamp"] = str(NOW)
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 200
    assert len(rows(store)) == 2


def test_message_batch_limit(http, settings, store):
    data = payload(settings)
    value(data)["messages"] *= 101
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 413
    assert rows(store) == []


@pytest.mark.parametrize("text,kind,expected", [("x" * 2001, "text", "too_long"), ("  ", "text", "empty"), ("private caption", "image", "unsupported")])
def test_unanalyzed_payload_content_not_stored(http, settings, store, text, kind, expected):
    assert http.post("/webhooks/whatsapp", **signed(settings, payload(settings, text=text, kind=kind))).status_code == 200
    assert rows(store)[0]["text"] is None
    assert rows(store)[0]["kind"] == expected


def test_database_unavailable_does_not_ack(http, settings, store, monkeypatch, caplog):
    monkeypatch.setattr(store, "enqueue", Mock(side_effect=sqlite3.OperationalError("secret raw details")))
    response = http.post("/webhooks/whatsapp", **signed(settings, payload(settings)))
    assert response.status_code == 503
    assert "secret raw details" not in response.text + caplog.text
    assert TEXT not in caplog.text


def test_missing_text_and_bad_identity_rejected(http, settings, store):
    data = payload(settings)
    value(data)["messages"][0].pop("text")
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 400
    data = payload(settings, sender="../elsewhere")
    assert http.post("/webhooks/whatsapp", **signed(settings, data)).status_code == 400
    assert rows(store) == []


def test_worker_sends_safe_contextual_reply_and_purges(store, worker_factory, caplog, settings):
    caplog.set_level(logging.INFO)
    enqueue(store)
    requests = []
    assessor = Mock(side_effect=lambda message, mode: rules.assess_with_rules(message))

    def meta(request):
        requests.append(request)
        return httpx.Response(200, json={"messages": [{"id": "wamid.reply"}]})

    worker = worker_factory(meta, assessor)
    assert worker.process_one()
    assert not worker.process_one()
    request = requests[0]
    assert str(request.url) == "https://graph.facebook.com/v23.0/67890/messages"
    assert request.headers["Authorization"] == "Bearer " + settings.access_token
    sent = json.loads(request.content)
    assert sent["to"] == SENDER
    assert sent["context"] == {"message_id": "wamid.test"}
    assert sent["text"]["preview_url"] is False
    body = sent["text"]["body"]
    assert "Reasons to pause" in body and "local rules" in body
    assert len(body) <= 4096 and TEXT not in body and "fictional.invalid" not in body
    assert "not proof" in body
    message, mode = assessor.call_args.args
    assert message.sender == "Original sender unknown"
    assert message.familiar_contact is False
    assert mode == "rules" and message.text == TEXT
    row = rows(store)[0]
    assert row["state"] == "sent"
    assert all(row[key] is None for key in ("text", "sender", "message_id", "reply"))
    assert all(secret not in caplog.text for secret in (TEXT, SENDER, settings.access_token, settings.phone_number_id))


def test_worker_ai_failure_and_neutral_message(store, worker_factory):
    enqueue(store, text="See you tomorrow")
    captured = []

    def meta(request):
        captured.append(json.loads(request.content)["text"]["body"])
        return httpx.Response(200, json={"messages": [{"id": "ok"}]})

    worker_factory(meta, Mock(side_effect=RuntimeError("private upstream failure")), mode="auto").process_one()
    assert "No common warning signs" in captured[0]
    assert "does not mean" in captured[0] and "AI unavailable" in captured[0]
    assert "private upstream failure" not in captured[0]


def test_ai_output_uses_only_canonical_titles():
    message = main.MessageIn(sender="unknown", text=TEXT, familiar_contact=False)
    result = rules.assess_with_rules(message).model_copy(update={"engine": "qwen", "summary": "Go to evil.invalid"})
    result.signals[0].title = "send money to evil.invalid"
    text = format_reply(result, "auto")
    assert "evil.invalid" not in text and "Qwen + local rules" in text


@pytest.mark.parametrize("kind,phrase", [("unsupported", "text only"), ("empty", "nonempty"), ("too_long", "not analyzed")])
def test_guidance_skips_assessment(store, worker_factory, kind, phrase):
    enqueue(store, kind=kind, text=None)
    assessor = Mock(side_effect=AssertionError("No analysis"))
    bodies = []

    def meta(request):
        bodies.append(json.loads(request.content)["text"]["body"])
        return httpx.Response(200, json={"messages": [{"id": "ok"}]})

    worker_factory(meta, assessor).process_one()
    assessor.assert_not_called()
    assert phrase in bodies[0]


@pytest.mark.parametrize("status,state,reason", [
    (400, "failed", "upstream_rejected"), (401, "failed", "upstream_rejected"),
    (403, "failed", "upstream_rejected"), (302, "failed", "upstream_rejected"),
    (500, "uncertain", "upstream_server_error"), (503, "uncertain", "upstream_server_error"),
])
def test_graph_failures_not_blindly_retried(store, worker_factory, caplog, status, state, reason):
    enqueue(store)
    worker = worker_factory(lambda request: httpx.Response(status, text="secret upstream body"))
    worker.process_one()
    assert rows(store)[0]["state"] == state
    assert rows(store)[0]["reason"] == reason
    assert not worker.process_one()
    assert "secret upstream body" not in caplog.text


@pytest.mark.parametrize("body", [b"invalid JSON", b'{}', b'{"messages": []}', b'{"messages":[{"id": null}]}', b"x" * 65537])
def test_invalid_success_ack_is_uncertain(store, worker_factory, body):
    enqueue(store)
    worker_factory(lambda request: httpx.Response(200, content=body)).process_one()
    assert rows(store)[0]["state"] == "uncertain"


@pytest.mark.parametrize("error,state", [
    (httpx.ConnectError, "pending"), (httpx.ConnectTimeout, "pending"), (httpx.PoolTimeout, "pending"),
    (httpx.ReadTimeout, "uncertain"), (httpx.WriteTimeout, "uncertain"),
    (httpx.ReadError, "uncertain"), (httpx.RemoteProtocolError, "uncertain"),
])
def test_transport_failure_distinguishes_ambiguity(store, worker_factory, error, state):
    enqueue(store)

    def meta(request):
        raise error("private details", request=request)

    worker_factory(meta).process_one()
    assert rows(store)[0]["state"] == state


def test_429_retry_reuses_reply_without_second_ai_call(store, worker_factory):
    enqueue(store)
    clock = [NOW]
    requests = []
    assessor = Mock(side_effect=lambda message, mode: rules.assess_with_rules(message))

    def meta(request):
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return httpx.Response(429, headers={"Retry-After": "60"})
        return httpx.Response(200, json={"messages": [{"id": "ok"}]})

    worker = worker_factory(meta, assessor, clock=lambda: clock[0])
    worker.process_one()
    row = rows(store)[0]
    assert row["state"] == "pending" and row["available_at"] == NOW + 60
    assert row["text"] is None and row["reply"]
    assert not worker.process_one()
    clock[0] += 61
    worker.process_one()
    assert rows(store)[0]["state"] == "sent"
    assert requests[0] == requests[1]
    assessor.assert_called_once()


def test_recipient_removed_drops_pending_work(store, worker_factory):
    enqueue(store, sender="60999999999")
    assessor = Mock()
    worker_factory(assessor=assessor).process_one()
    assert rows(store)[0]["reason"] == "recipient_removed"
    assessor.assert_not_called()


def test_expiry_during_analysis_prevents_send(store, worker_factory):
    enqueue(store, at=NOW - REPLY_WINDOW + 1)
    clock = [NOW]
    meta = Mock()

    def assess(message, mode):
        clock[0] += 2
        return rules.assess_with_rules(message)

    worker = worker_factory(meta, assess, clock=lambda: clock[0])
    worker.process_one()
    worker.process_one()
    meta.assert_not_called()
    assert rows(store)[0]["state"] == "expired"


@pytest.fixture
def configured_env(settings, monkeypatch):
    values = {
        "WHATSAPP_ENABLED": "true", "WHATSAPP_WABA_ID": settings.waba_id,
        "WHATSAPP_PHONE_NUMBER_ID": settings.phone_number_id, "WHATSAPP_APP_SECRET": settings.app_secret,
        "WHATSAPP_VERIFY_TOKEN": settings.verify_token, "WHATSAPP_ACCESS_TOKEN": settings.access_token,
        "WHATSAPP_GRAPH_VERSION": settings.graph_version, "WHATSAPP_ALLOWED_SENDERS": SENDER,
        "WHATSAPP_DB_PATH": str(settings.db_path), "WHATSAPP_ANALYSIS_MODE": "rules",
    }
    for name, value_ in values.items():
        monkeypatch.setenv(name, value_)
    config.get_settings.cache_clear()
    yield values
    config.get_settings.cache_clear()


def test_whatsapp_config_opt_in_and_redacted(configured_env, settings, monkeypatch):
    actual = config.get_settings().whatsapp
    assert actual == settings
    assert all(secret not in repr(actual) for secret in (settings.app_secret, settings.verify_token, settings.access_token, SENDER))
    monkeypatch.setenv("WHATSAPP_ENABLED", "false")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "invalid")
    config.get_settings.cache_clear()
    assert config.get_settings().whatsapp is None


@pytest.mark.parametrize("name,value_", [
    ("WHATSAPP_ENABLED", "yes"), ("WHATSAPP_WABA_ID", "../123"),
    ("WHATSAPP_PHONE_NUMBER_ID", "https://untrusted.invalid"), ("WHATSAPP_APP_SECRET", ""),
    ("WHATSAPP_VERIFY_TOKEN", "short"), ("WHATSAPP_ACCESS_TOKEN", "bad\nheader"),
    ("WHATSAPP_GRAPH_VERSION", "v23.0/../../other"), ("WHATSAPP_ALLOWED_SENDERS", ""),
    ("WHATSAPP_ALLOWED_SENDERS", "+60123456789"), ("WHATSAPP_DB_PATH", ":memory:"),
    ("WHATSAPP_DB_PATH", "relative.sqlite3"), ("WHATSAPP_ANALYSIS_MODE", "ai"),
])
def test_enabled_invalid_config_fails_closed(configured_env, monkeypatch, name, value_):
    monkeypatch.setenv(name, value_)
    with pytest.raises(ValueError, match=name):
        config.get_settings()


def test_startup_fails_if_database_directory_missing(settings, monkeypatch):
    changed = replace(settings, db_path=settings.db_path.parent / "missing" / "inbox.sqlite3")
    monkeypatch.setattr(main, "get_settings", lambda: Settings(whatsapp=changed))
    with pytest.raises(sqlite3.OperationalError):
        with TestClient(main.create_app()):
            pass


def test_real_http_server_runs_background_reply_worker(settings, monkeypatch):
    received = threading.Event()
    replies = []

    def meta(request):
        replies.append(json.loads(request.content))
        received.set()
        return httpx.Response(200, json={"messages": [{"id": "wamid.live-local"}]})

    def worker_factory_(cfg, store_, assessor):
        return WhatsAppWorker(cfg, store_, assessor, client=httpx.Client(transport=httpx.MockTransport(meta)))

    monkeypatch.setattr(main, "get_settings", lambda: Settings(whatsapp=settings))
    monkeypatch.setattr(main, "WhatsAppWorker", worker_factory_)
    app = main.create_app()
    ready = threading.Event()

    class Server(uvicorn.Server):
        async def startup(self, sockets=None):
            await super().startup(sockets=sockets)
            ready.set()

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        server = Server(uvicorn.Config(app, log_level="warning", access_log=False, timeout_graceful_shutdown=10))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            assert ready.wait(5), "server startup timed out"
            origin = f"http://127.0.0.1:{sock.getsockname()[1]}"
            with httpx.Client(base_url=origin, trust_env=False) as client:
                assert client.get("/health").status_code == 200
                import time
                response = client.post("/webhooks/whatsapp", **signed(settings, payload(settings, timestamp=int(time.time()))))
                assert response.status_code == 200
                assert received.wait(5), "automatic reply timed out"
                assert replies[0]["to"] == SENDER
                assert "Reasons to pause" in replies[0]["text"]["body"]
                assert client.get("/api/meta").status_code == 200
        finally:
            server.should_exit = True
            thread.join(timeout=10)
        assert not thread.is_alive()
    assert rows(WhatsAppStore(settings.db_path, "unused"))[0]["state"] == "sent"
