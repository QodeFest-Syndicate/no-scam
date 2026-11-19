import pytest
from fastapi.testclient import TestClient

from src.service.ai import qwen
from src.service.main import app

client = TestClient(app)

SCAM_TEXT = (
    "Hi Mak, it's me Amir. I need your help urgently! My bank account has a "
    "problem and I need to pay RM500 right now. Please use this link to help "
    "me: https://urgent-family-pay.example Please don't call me, I'm in a "
    "meeting. Just do it quickly!"
)


def payload(text=SCAM_TEXT):
    return {
        "message": {
            "sender": "Amir (Son)",
            "familiarContact": True,
            "channel": "whatsapp",
            "text": text,
        }
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["uptime"], (int, float))


def test_meta_states_demo_boundaries():
    response = client.get("/api/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "no-scam"
    assert body["demoDataOnly"] is True
    assert body["aiEnabled"] is False
    assert body["engine"] == "rules"


def test_scenario_endpoint_returns_the_demo_message():
    body = client.get("/api/scenarios").json()
    assert len(body["scenarios"]) == 1
    scenario = body["scenarios"][0]
    assert scenario["id"] == "amir-payment"
    assert scenario["message"]["familiarContact"] is True
    assert "urgent-family-pay.example" in scenario["message"]["text"]


def test_assess_scam_message_in_rules_mode():
    response = client.post("/api/assess?mode=rules", json=payload())
    assert response.status_code == 200
    assessment = response.json()["assessment"]
    assert assessment["level"] == "pause"
    assert assessment["engine"] == "rules"
    assert assessment["aiAvailable"] is False
    assert [signal["id"] for signal in assessment["signals"]] == [
        "urgency",
        "link",
        "money",
        "secrecy",
    ]
    assert assessment["signals"][0]["icon"] == "⏱"
    assert "familiar" in assessment["summary"]
    assert "not proof" in assessment["disclaimer"]
    checks = {check["id"]: check for check in assessment["checks"]}
    assert checks["link"]["status"] == "unavailable"


def test_assess_benign_message():
    response = client.post(
        "/api/assess",
        json=payload("Hi Mak, see you at 3pm. Call me later."),
    )
    assert response.status_code == 200
    assessment = response.json()["assessment"]
    assert assessment["level"] == "no_signals"
    assert assessment["signals"] == []
    assert "not proof" in assessment["summary"]


def test_assess_ignores_unknown_fields_and_accepts_snake_case():
    request = {
        "message": {
            "sender": "Amir (Son)",
            "familiar_contact": True,
            "text": SCAM_TEXT,
            "unexpected": "ignored",
        },
        "extra": "ignored",
    }
    response = client.post("/api/assess", json=request)
    assert response.status_code == 200


def test_assess_rejects_missing_and_oversized_text():
    assert client.post("/api/assess", json={"message": {"sender": "Amir"}}).status_code == 422
    assert client.post("/api/assess", json=payload("x" * 2001)).status_code == 422


def test_assess_rejects_unknown_mode():
    assert client.post("/api/assess?mode=magic", json=payload()).status_code == 422


def test_auto_mode_falls_back_without_key():
    response = client.post("/api/assess?mode=auto", json=payload())
    assert response.status_code == 200
    assessment = response.json()["assessment"]
    assert assessment["engine"] == "rules"
    assert assessment["aiAvailable"] is False


def test_ai_mode_is_strict_without_key():
    response = client.post("/api/assess?mode=ai", json=payload())
    assert response.status_code == 503
    assert "mode=auto" in response.json()["detail"]


def test_auto_mode_falls_back_when_qwen_raises(monkeypatch):
    def explode(message, fallback):
        raise RuntimeError("network down")

    monkeypatch.setattr(qwen, "assess_with_qwen", explode)
    response = client.post("/api/assess?mode=auto", json=payload())
    assert response.status_code == 200
    assessment = response.json()["assessment"]
    assert assessment["engine"] == "rules"
    assert assessment["level"] == "pause"


def test_ai_mode_returns_503_when_qwen_raises(monkeypatch):
    def explode(message, fallback):
        raise RuntimeError("network down")

    monkeypatch.setattr(qwen, "assess_with_qwen", explode)
    response = client.post("/api/assess?mode=ai", json=payload())
    assert response.status_code == 503
    assert "mode=auto" in response.json()["detail"]


def test_ai_assessment_is_used_when_available(monkeypatch):
    def enrich(message, fallback):
        return fallback.model_copy(update={"engine": "qwen", "ai_available": True})

    monkeypatch.setattr(qwen, "assess_with_qwen", enrich)
    response = client.post("/api/assess?mode=ai", json=payload())
    assert response.status_code == 200
    assessment = response.json()["assessment"]
    assert assessment["engine"] == "qwen"
    assert assessment["aiAvailable"] is True


@pytest.mark.parametrize(
    "incident",
    ["clicked_link", "entered_credentials", "sent_money", "shared_info"],
)
def test_recovery_returns_ordered_steps_and_helpline(incident):
    response = client.post("/api/recovery", json={"incident": incident})
    assert response.status_code == 200
    body = response.json()
    assert body["incident"] == incident
    assert body["steps"]
    assert [step["order"] for step in body["steps"]] == list(range(1, len(body["steps"]) + 1))
    assert "997" in body["disclaimer"]
    assert "do not guarantee" in body["disclaimer"]


def test_sent_money_recovery_leads_with_bank_and_997():
    body = client.post("/api/recovery", json={"incident": "sent_money"}).json()
    assert body["steps"][0]["urgent"] is True
    joined = " ".join(
        f"{step['title']} {step['detail']}" for step in body["steps"]
    )
    assert "bank" in joined.lower()
    assert "997" in joined


def test_recovery_rejects_unknown_incident():
    assert client.post("/api/recovery", json={"incident": "lost_wallet"}).status_code == 422
