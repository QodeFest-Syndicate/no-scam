"""Deterministic demo rules.

Ported from the scripted UI's ``getWarningSignals`` so the HTTP backend and
the offline UI fallback stay aligned. These are reasons to pause, never a
verdict about the sender or the link.
"""

from __future__ import annotations

import re

from .types import Assessment, Check, MessageIn, Signal

DISCLAIMER = (
    "These are warning signs, not proof of a scam. We have not verified who "
    "sent this message, inspected the link, or contacted anyone."
)

SIGNAL_ORDER: tuple[str, ...] = ("urgency", "link", "money", "secrecy")

_SIGNAL_TEXT: dict[str, tuple[str, str, str]] = {
    "urgency": (
        "⏱",
        "Pressure to act quickly",
        "The message says it is urgent and asks you to act before checking.",
    ),
    "link": (
        "🔗",
        "Link has not been verified",
        "The link is not a destination we have independently checked.",
    ),
    "money": (
        "💳",
        "Unusual money request",
        "You are being asked to send money or use a payment link.",
    ),
    "secrecy": (
        "🙊",
        "Discourages independent verification",
        "The sender asks you not to call, making it harder to check who is really asking.",
    ),
}

_PATTERNS: dict[str, re.Pattern[str]] = {
    "urgency": re.compile(r"urgently|right now|quickly|immediately|segera", re.IGNORECASE),
    "link": re.compile(r"https?://\S+", re.IGNORECASE),
    "money": re.compile(r"rm\s*\d+|pay|transfer|bank account", re.IGNORECASE),
    "secrecy": re.compile(r"don't call|do not call|don't tell|keep.*secret", re.IGNORECASE),
}


def canonical_signal(signal_id: str, detail: str | None = None) -> Signal:
    icon, title, default_detail = _SIGNAL_TEXT[signal_id]
    return Signal(
        id=signal_id,
        icon=icon,
        title=title,
        detail=detail or default_detail,
    )


def find_signals(text: str) -> list[Signal]:
    return [
        canonical_signal(signal_id)
        for signal_id in SIGNAL_ORDER
        if _PATTERNS[signal_id].search(text)
    ]


def _summary(message: MessageIn, signals: list[Signal]) -> str:
    if signals:
        if message.familiar_contact:
            return (
                f"{message.sender} may be a familiar contact, but this request "
                "is not verified. Pause and check through a route you already trust."
            )
        return (
            "This message contains warning signs. Pause and check through a "
            "route you already trust before you act."
        )
    return (
        "We did not find the warning signs this demo checks for. That is not "
        "proof the message is safe. If it asks for money, account details or a "
        "login, verify it independently before you act."
    )


def build_checks(message: MessageIn, signals: list[Signal], engine: str) -> list[Check]:
    if engine == "qwen":
        text_check = Check(
            id="text_signals",
            label="Qwen interpretation of the message text",
            source="Qwen via DashScope (AI)",
            status="completed",
            result=(
                f"{len(signals)} warning sign(s) explained."
                if signals
                else "No warning signs identified."
            ),
        )
    else:
        text_check = Check(
            id="text_signals",
            label="Warning-sign scan of the message text",
            source="Demo rules (local, deterministic)",
            status="completed",
            result=(
                f"{len(signals)} warning sign(s) found."
                if signals
                else "No known warning signs found."
            ),
        )

    if _PATTERNS["link"].search(message.text):
        link_check = Check(
            id="link",
            label="Link destination inspection",
            source="Not available in this demo",
            status="unavailable",
            result="The link was not opened, fetched or scanned.",
        )
    else:
        link_check = Check(
            id="link",
            label="Link destination inspection",
            source="Not available in this demo",
            status="not_run",
            result="No link was found in the message.",
        )

    if message.familiar_contact:
        contact_check = Check(
            id="contact",
            label=f"Independent check with {message.sender}",
            source="A route you already trust — you confirm",
            status="not_run",
            result=(
                f"Call {message.sender} on a saved number, or ask another family "
                "member to check. Do not use contact details from this message."
            ),
        )
    else:
        contact_check = Check(
            id="contact",
            label="Independent sender check",
            source="A route you already trust — you confirm",
            status="not_run",
            result=(
                "Confirm who sent this through a known number or official "
                "channel before you act."
            ),
        )

    return [text_check, link_check, contact_check]


def assess_with_rules(message: MessageIn) -> Assessment:
    signals = find_signals(message.text)
    return Assessment(
        level="pause" if signals else "no_signals",
        engine="rules",
        signals=signals,
        summary=_summary(message, signals),
        disclaimer=DISCLAIMER,
        ai_available=False,
        checks=build_checks(message, signals, "rules"),
    )
