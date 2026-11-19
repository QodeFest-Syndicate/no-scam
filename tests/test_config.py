from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.service.ai import qwen
from src.service.config import get_settings
from src.service.main import create_app


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    for name in (
        "DASHSCOPE_API_KEY", "DASHSCOPE_BASE_URL", "QWEN_MODEL", "AI_TIMEOUT_MS",
        "QODER_API_KEY", "QODER_HOST", "OPENAI_ENDPOINT", "OPENAI_BASE_URL",
        "OPENAI_API_KEY", "WATCHDOG_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def configure_gateway(monkeypatch):
    monkeypatch.setenv("QODER_API_KEY", "test-qoder-key")
    monkeypatch.setenv("QODER_HOST", "https://gateway.example/")
    monkeypatch.setenv("OPENAI_ENDPOINT", "/compatible-mode/v1")


def test_missing_keys_disable_ai():
    assert get_settings().ai_enabled is False


def test_qoder_gateway_configuration(monkeypatch):
    configure_gateway(monkeypatch)
    settings = get_settings()
    assert settings.ai_enabled is True
    assert settings.dashscope_api_key == "test-qoder-key"
    assert settings.dashscope_base_url == "https://gateway.example/compatible-mode/v1"
    assert settings.qwen_model == "qwen3.8-flash"
    assert settings.ai_timeout_ms == 30000


def test_gateway_host_without_scheme(monkeypatch):
    configure_gateway(monkeypatch)
    monkeypatch.setenv("QODER_HOST", "gateway.example")
    assert get_settings().dashscope_base_url == "https://gateway.example/compatible-mode/v1"


def test_explicit_openai_url_and_model(monkeypatch):
    configure_gateway(monkeypatch)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://explicit.example/v1/")
    monkeypatch.setenv("WATCHDOG_MODEL", "configured-model")
    settings = get_settings()
    assert settings.dashscope_base_url == "https://explicit.example/v1"
    assert settings.qwen_model == "configured-model"


def test_openai_key_with_explicit_endpoint(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    assert get_settings().ai_enabled is True
    assert get_settings().dashscope_api_key == "test-openai-key"


def test_gateway_key_without_endpoint_does_not_use_dashscope(monkeypatch):
    monkeypatch.setenv("QODER_API_KEY", "test-qoder-key")
    assert get_settings().ai_enabled is False


def test_gateway_endpoint_without_key_disables_ai(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    assert get_settings().ai_enabled is False


def test_direct_dashscope_takes_precedence(monkeypatch):
    configure_gateway(monkeypatch)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")
    monkeypatch.setenv("WATCHDOG_MODEL", "gateway-only-model")
    settings = get_settings()
    assert settings.dashscope_api_key == "test-dashscope-key"
    assert settings.dashscope_base_url == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    assert settings.qwen_model == "qwen-plus"
    assert settings.ai_timeout_ms == 8000


def test_direct_dashscope_overrides(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://custom.example/v1/")
    monkeypatch.setenv("QWEN_MODEL", "custom-qwen")
    settings = get_settings()
    assert settings.dashscope_base_url == "https://custom.example/v1"
    assert settings.qwen_model == "custom-qwen"


@pytest.mark.parametrize("value, expected", [("invalid", 30000), ("999999", 30000), ("-1", 1000), ("15000", 15000)])
def test_gateway_timeout_is_bounded(monkeypatch, value, expected):
    configure_gateway(monkeypatch)
    monkeypatch.setenv("AI_TIMEOUT_MS", value)
    assert get_settings().ai_timeout_ms == expected


def test_gateway_http_assessment_uses_configured_client(monkeypatch):
    configure_gateway(monkeypatch)
    completion = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=(
        '{"signals": [], "summary": "Pause and call through a saved contact."}'
    )))])
    create = Mock(return_value=completion)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    factory = Mock(return_value=client)
    monkeypatch.setattr(qwen, "OpenAI", factory)
    with TestClient(create_app()) as http:
        meta = http.get("/api/meta")
        assert meta.json()["aiEnabled"] is True
        assert "test-qoder-key" not in meta.text
        scenario = http.get("/api/scenarios").json()["scenarios"][0]
        response = http.post("/api/assess?mode=ai", json={"message": scenario["message"]})
        assert response.status_code == 200
        assessment = response.json()["assessment"]
        assert assessment["engine"] == "qwen"
        assert assessment["aiAvailable"] is True
        assert [s["id"] for s in assessment["signals"]] == ["urgency", "link", "money", "secrecy"]
        assert "test-qoder-key" not in response.text
    factory.assert_called_once_with(
        api_key="test-qoder-key",
        base_url="https://gateway.example/compatible-mode/v1",
        timeout=30.0,
        max_retries=0,
    )
    assert create.call_args.kwargs["model"] == "qwen3.8-flash"
    assert scenario["message"]["text"] in create.call_args.kwargs["messages"][1]["content"]


def test_gateway_failure_is_strict_or_explicitly_rules(monkeypatch):
    configure_gateway(monkeypatch)
    factory = Mock(side_effect=RuntimeError("unreachable"))
    monkeypatch.setattr(qwen, "OpenAI", factory)
    with TestClient(create_app()) as http:
        scenario = http.get("/api/scenarios").json()["scenarios"][0]
        payload = {"message": scenario["message"]}
        assert http.post("/api/assess?mode=ai", json=payload).status_code == 503
        automatic = http.post("/api/assess?mode=auto", json=payload).json()["assessment"]
        assert automatic["engine"] == "rules"
        assert automatic["aiAvailable"] is False
        factory.reset_mock()
        rules = http.post("/api/assess?mode=rules", json=payload).json()["assessment"]
        assert rules["engine"] == "rules"
        factory.assert_not_called()
