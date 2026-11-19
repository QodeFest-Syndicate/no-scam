import pytest

from src.service.ai.qwen import build_qwen_assessment
from src.service.domain import rules
from src.service.domain.types import MessageIn

TEXT = (
    "Hi Mak, it's me Amir. I need your help urgently! Pay RM500 at "
    "https://urgent-family-pay.example and please don't call me."
)


def fallback_assessment():
    return rules.assess_with_rules(MessageIn(sender="Amir (Son)", text=TEXT))


def test_qwen_detail_is_used_but_rule_signals_are_never_dropped():
    payload = {
        "signals": [{"id": "urgency", "detail": "The message says 'urgently' and asks you to act now."}],
        "summary": "This request is not verified. Call Amir on a number you already saved before doing anything.",
    }
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        payload,
        fallback_assessment(),
    )
    assert result is not None
    assert result.engine == "qwen"
    assert result.ai_available is True
    assert [signal.id for signal in result.signals] == ["urgency", "link", "money", "secrecy"]
    urgency = next(signal for signal in result.signals if signal.id == "urgency")
    assert urgency.detail.startswith("The message says 'urgently'")
    assert result.summary.startswith("This request is not verified")


def test_unknown_signal_ids_are_ignored():
    payload = {
        "signals": [
            {"id": "source", "detail": "This came from an official source."},
            {"id": "link", "detail": "The link is new."},
        ],
        "summary": "Pause and check through a route you trust.",
    }
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        payload,
        fallback_assessment(),
    )
    assert result is not None
    assert all(signal.id in rules.SIGNAL_ORDER for signal in result.signals)


def test_verdict_language_in_summary_falls_back_to_rules_summary():
    fallback = fallback_assessment()
    payload = {
        "signals": [{"id": "urgency", "detail": "It asks you to act immediately."}],
        "summary": "This is definitely a scam.",
    }
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        payload,
        fallback,
    )
    assert result is not None
    assert result.summary == fallback.summary


def test_verdict_language_in_detail_falls_back_to_canonical_detail():
    payload = {
        "signals": [{"id": "urgency", "detail": "This is a scam and is 100% guaranteed."}],
        "summary": "Pause and check through a route you trust.",
    }
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        payload,
        fallback_assessment(),
    )
    assert result is not None
    urgency = next(signal for signal in result.signals if signal.id == "urgency")
    assert urgency.detail == rules.canonical_signal("urgency").detail


def test_malformed_signals_shape_is_rejected():
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        {"signals": "urgency", "summary": "..."},
        fallback_assessment(),
    )
    assert result is None


@pytest.mark.parametrize(
    "summary",
    [
        "This is not a scam.",
        "This message is genuine.",
        "It looks legitimate, go ahead.",
        "It is safe to pay now.",
        "This is a trusted sender.",
        "The identity is verified.",
    ],
)
def test_reassurance_language_falls_back_to_rules_summary(summary):
    fallback = fallback_assessment()
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        {"signals": [], "summary": summary},
        fallback,
    )
    assert result is not None
    assert result.summary == fallback.summary


def test_uncertainty_language_is_allowed():
    summary = "This request has not been verified. Call Amir on a number you already saved."
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        {"signals": [], "summary": summary},
        fallback_assessment(),
    )
    assert result is not None
    assert result.summary == summary


@pytest.mark.parametrize(
    "contact",
    [
        "Call 012-345 6789 to confirm.",
        "Visit https://verify-amir.example for help.",
        "Email help@verify-amir.example for details.",
        "Go to verify-amir.example to check.",
    ],
)
def test_contact_details_in_detail_use_canonical_text(contact):
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        {"signals": [{"id": "urgency", "detail": contact}], "summary": "Pause and check."},
        fallback_assessment(),
    )
    assert result is not None
    urgency = next(signal for signal in result.signals if signal.id == "urgency")
    assert urgency.detail == rules.canonical_signal("urgency").detail


def test_contact_details_in_summary_fall_back_to_rules_summary():
    fallback = fallback_assessment()
    result = build_qwen_assessment(
        MessageIn(sender="Amir (Son)", text=TEXT),
        {
            "signals": [{"id": "urgency", "detail": "It asks you to act immediately."}],
            "summary": "Call 012-345 6789 to confirm before you act.",
        },
        fallback,
    )
    assert result is not None
    assert result.summary == fallback.summary
