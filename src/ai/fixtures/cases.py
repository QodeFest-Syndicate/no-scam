"""Scripted demo scenarios. All names, numbers, links and amounts are fictional."""

from __future__ import annotations

from ..schemas import AssessmentRequest

_SCENARIOS: dict[str, dict] = {
    "familiar-link": {
        "title": "Familiar account, urgent delivery fee and a new link",
        "user_label": "Puan Salmah",
        "incident": {
            "channel": "whatsapp",
            "sender_display_name": "Mak Cik Zana",
            "sender_handle": "+60 12-345 6789",
            "message_text": (
                "Salmah, urgent! The courier is holding my parcel. Pay the RM45 delivery "
                "fee here https://parcel-redelivery-my.top/pay?id=8821 and send me the "
                "receipt. Don't tell Aminah yet, she will worry. Do it now before 5pm."
            ),
            "perimeter": [
                {
                    "name": "Mak Cik Zana",
                    "relationship": "sister",
                    "known_handles": ["+60 12-345 6789"],
                    "known_channels": ["whatsapp", "call"],
                    "shares_secret_word": True,
                },
                {
                    "name": "Aminah",
                    "relationship": "daughter",
                    "known_handles": ["+60 17-222 3344"],
                    "known_channels": ["whatsapp", "call"],
                },
            ],
        },
    },
    "voice-clone-call": {
        "title": "Voice call claiming to be the son, on a new number",
        "user_label": "Puan Salmah",
        "incident": {
            "channel": "call",
            "sender_display_name": "Daniel",
            "sender_handle": "+60 11-2233 4455",
            "message_text": (
                "Mum, it's Daniel. I lost my phone, this is my new number. I'm in trouble "
                "at the workshop and I need RM4,800 today. Please transfer now. Don't call "
                "my old number, it's off. Don't tell Ayah yet."
            ),
            "perimeter": [
                {
                    "name": "Daniel",
                    "relationship": "son",
                    "known_handles": ["+60 19-888 7766"],
                    "known_channels": ["call", "whatsapp"],
                    "shares_secret_word": True,
                }
            ],
        },
    },
    "already-clicked": {
        "title": "Already clicked and shared an OTP",
        "user_label": "Uncle Lim",
        "incident": {
            "channel": "sms",
            "sender_display_name": "MYparcel",
            "sender_handle": "+60 13-000 1111",
            "message_text": (
                "Your parcel is held. Pay the RM2.50 redelivery fee at "
                "https://secure-maybank-verify.info/track and enter your online banking "
                "username and OTP to release it."
            ),
            "already_acted": True,
            "acted_details": (
                "I tapped the link, typed my online banking username and the OTP that came "
                "by SMS."
            ),
            "evidence": [
                {
                    "subject": "secure-maybank-verify.info",
                    "verdict": "reported",
                    "source": "service:demo-report-check",
                    "detail": "Listed twice in the report feed for bank-login imitation.",
                    "confidence": 0.72,
                }
            ],
        },
    },
    "benign-family-message": {
        "title": "Control case: ordinary message on a saved route",
        "user_label": "Puan Salmah",
        "incident": {
            "channel": "whatsapp",
            "sender_display_name": "Daniel",
            "sender_handle": "+60 19-888 7766",
            "message_text": (
                "Mak, I'll pick you up at six. Bring the umbrella, looks like rain. "
                "No need to cook tonight."
            ),
            "perimeter": [
                {
                    "name": "Daniel",
                    "relationship": "son",
                    "known_handles": ["+60 19-888 7766"],
                    "known_channels": ["call", "whatsapp"],
                    "shares_secret_word": True,
                }
            ],
        },
    },
}

DEMO_NAMES: tuple[str, ...] = tuple(_SCENARIOS)


def list_cases() -> list[tuple[str, str]]:
    return [(name, payload["title"]) for name, payload in _SCENARIOS.items()]


def load_case(name: str) -> AssessmentRequest:
    """Return a validated request for a scripted scenario."""
    if name not in _SCENARIOS:
        raise KeyError(name)
    return AssessmentRequest.model_validate(_SCENARIOS[name])
