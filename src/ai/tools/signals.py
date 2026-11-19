"""Observable-clue extraction and the rule-based risk floor.

This module is the non-negotiable part of the swarm: no model can push the
verdict below what these visible clues justify. It also gives the demo a fully
offline path (``WATCHDOG_LLM=offline``).
"""

from __future__ import annotations

import re

from ..schemas import AssessmentRequest, IncidentProfile, RiskLevel
from .perimeter import handles_match, match_contact, route_is_known
from .reputation import extract_links

URGENCY_TERMS = (
    "urgent", "urgently", "right now", "immediately", "asap", "today only",
    "before tonight", "quick", "hurry", "segera", "cepat", "sekarang",
    "hari ini", "sebelum",
)
SECRECY_TERMS = (
    "don't tell", "do not tell", "dont tell", "keep this between", "no one else",
    "just between us", "secret", "jangan beritahu", "jangan bagitahu",
    "jangan cakap", "rahsia", "jangan beritau",
)
AUTHORITY_TERMS = (
    "bank", "police", "lhdn", "customs", "court", "officer", "pegawai",
    "mahkamah", "polis", "kastam", "tribunal",
)
CREDENTIAL_TERMS = (
    "otp", "password", "passcode", "pin number", "tac", "cvv", "kata laluan",
    "kod otp", "log in", "login",
)
MONEY_TERMS = (
    "transfer", "send money", "pay", "payment", "deposit", "duit", "wang",
    "bayar", "pinjam", "loan", "ringgit",
)
NEW_NUMBER_TERMS = (
    "new number", "nombor baru", "this is my new", "lost my phone",
    "hilang telefon", "phone broke", "telefon rosak", "temporary number",
)

_MONEY_AMOUNT = re.compile(r"\brm\s?([0-9][0-9,]*(?:\.[0-9]{1,2})?)\b", re.I)


def _hits(text: str, terms: tuple[str, ...]) -> list[str]:
    """Short tokens need word boundaries ('tac' must not match 'contact')."""
    matched: list[str] = []
    for term in terms:
        if " " not in term and len(term) <= 4:
            pattern = re.compile(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", re.I)
            if pattern.search(text):
                matched.append(term)
        elif term in text:
            matched.append(term)
    return matched


def _bands(score: int) -> RiskLevel:
    if score >= 60:
        return RiskLevel.high
    if score >= 30:
        return RiskLevel.elevated
    return RiskLevel.low


def detect_amount(text: str, declared: float | None) -> float | None:
    if declared is not None:
        return declared
    match = _MONEY_AMOUNT.search(text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def analyze_incident(request: AssessmentRequest) -> IncidentProfile:
    """Build the deterministic profile the whole swarm reasons from."""
    incident = request.incident
    text = (incident.message_text or "").lower()

    contact = match_contact(
        handle=incident.sender_handle,
        display_name=incident.sender_display_name,
        perimeter=incident.perimeter,
    )
    sender_known = bool(incident.sender_handle) and contact is not None and any(
        handles_match(incident.sender_handle or "", known) for known in contact.known_handles
    )
    known_route = sender_known and route_is_known(contact, incident.channel)

    links = list(dict.fromkeys([*incident.links, *extract_links(incident.message_text)]))
    unfamiliar = [link for link in links if not _link_is_familiar(link, contact)]

    amount = detect_amount(incident.message_text, incident.amount_myr)
    money_requested = bool(_hits(text, MONEY_TERMS)) or amount is not None
    urgency = _hits(text, URGENCY_TERMS)
    secrecy = _hits(text, SECRECY_TERMS)
    authority = _hits(text, AUTHORITY_TERMS)
    credentials = _hits(text, CREDENTIAL_TERMS)
    new_number = _hits(text, NEW_NUMBER_TERMS)

    score = 0
    notes: list[str] = []

    if incident.sender_handle and not sender_known:
        score += 25
        notes.append("Sender route is not one you registered; only the display name is familiar.")
    if new_number:
        score += 15
        notes.append("The message claims a changed or new number - a classic handover script.")
    if money_requested:
        score += 20
        notes.append("Money is being requested.")
        if amount is not None and amount >= 500:
            score += 5
            notes.append(f"The amount (RM{amount:,.0f}) is large enough to hurt.")
    if urgency:
        score += 15
        notes.append("Time pressure is applied.")
    if secrecy:
        score += 15
        notes.append("Secrecy is requested, which blocks a second opinion.")
    if authority:
        score += 5
        notes.append("An authority claim appears in the message.")
    if credentials:
        score += 20
        notes.append("Credentials or login details are requested.")
    if unfamiliar:
        score += 20
        notes.append("The message introduces a link that is not part of your usual routine.")
    if not links and not money_requested and sender_known and known_route:
        score = min(score, 10)

    score = max(0, min(100, score))
    return IncidentProfile(
        channel=incident.channel,
        sender_handle=incident.sender_handle,
        sender_display_name=incident.sender_display_name,
        matched_contact=contact.name if contact else None,
        sender_known=sender_known,
        known_route=known_route,
        claims_new_number=bool(new_number),
        links=links,
        unfamiliar_links=unfamiliar,
        amount_myr=amount,
        money_requested=money_requested,
        urgency_hits=urgency,
        secrecy_hits=secrecy,
        authority_hits=authority,
        credential_hits=credentials,
        new_number_hits=new_number,
        already_acted=incident.already_acted,
        risk_score=score,
        baseline_band=_bands(score),
        notes=notes,
    )


def _link_is_familiar(link: str, contact) -> bool:
    """A link is 'familiar' only if the trusted contact routinely shares that domain."""
    if contact is None or not contact.known_link_domains:
        return False
    domain = re.sub(r"^https?://", "", link).split("/")[0].lower()
    return bool(domain) and any(
        domain == known.lower() or domain.endswith(f".{known.lower()}")
        for known in contact.known_link_domains
    )
