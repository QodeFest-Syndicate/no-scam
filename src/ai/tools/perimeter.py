"""Deterministic perimeter matching.

Trust here is about *routes*, not names: a familiar display name proves nothing,
but a handle the user registered earlier is a route they already trust.
"""

from __future__ import annotations

import re

from ..schemas import Channel, TrustedContact

_DIGITS = re.compile(r"\d+")


def normalize_handle(handle: str | None) -> str:
    return re.sub(r"[^\d+]", "", handle or "")


def normalize_name(name: str | None) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (name or "").lower()).strip()


def handles_match(left: str, right: str) -> bool:
    """Compare phone-like handles by their last 7 digits (country/prefix drift tolerant)."""
    a, b = normalize_handle(left), normalize_handle(right)
    if not a or not b:
        return False
    if a == b:
        return True
    a_tail, b_tail = re.sub(r"\D", "", a)[-7:], re.sub(r"\D", "", b)[-7:]
    return len(a_tail) == 7 and a_tail == b_tail


def match_contact(
    *,
    handle: str | None,
    display_name: str | None,
    perimeter: list[TrustedContact],
) -> TrustedContact | None:
    """Find the perimeter entry this sender claims, preferring handle evidence over names."""
    for contact in perimeter:
        for known in contact.known_handles:
            if handles_match(handle or "", known):
                return contact

    wanted = normalize_name(display_name)
    if not wanted:
        return None
    for contact in perimeter:
        candidate = normalize_name(contact.name)
        if candidate and (candidate == wanted or candidate in wanted or wanted in candidate):
            return contact
    return None


def route_is_known(contact: TrustedContact | None, channel: Channel) -> bool:
    """True only when the message arrived on a channel this contact normally uses."""
    if contact is None:
        return False
    if not contact.known_channels:
        return True  # perimeter entry declares no channel restriction
    return channel in contact.known_channels
