"""Simulated reputation lookup.

This is the swarm's only "tool" node. It is intentionally a local fixture table:
the POC must never imply a live tie-in to PDRM Semak Mule or a bank. When
``service`` supplies real evidence (fetched via ``mcp``), that evidence wins and
the local table is skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from ..schemas import EvidenceItem

_OFFICIAL_HINTS = ("gov.my", "maybank2u.com.my", "cimbclicks.com.my", "pbebank.com", "rhbgroup.com")

# Demo feed: fictional but plausible entries used by the scripted scenarios.
_DEMO_FEED: dict[str, tuple[str, str]] = {
    "parcel-redelivery-my.top": (
        "reported",
        "Listed 3 times in the local demo report feed (parcel fees + bank login lure).",
    ),
    "secure-maybank-verify.info": (
        "reported",
        "Listed in the local demo report feed as a bank-login imitation.",
    ),
    "kurnia-transport-pay.xyz": (
        "not_found",
        "No entry in the local demo feed. Absence of a report is not evidence of safety.",
    ),
}


@dataclass
class ReputationResult:
    subject: str
    verdict: str
    detail: str
    source: str
    confidence: float
    notes: list[str] = field(default_factory=list)


def domain_of(url: str) -> str:
    candidate = url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    try:
        return (urlparse(candidate).hostname or "").lower().lstrip(".")
    except ValueError:
        return ""


def _is_official(domain: str) -> bool:
    return any(domain == hint or domain.endswith(f".{hint}") for hint in _OFFICIAL_HINTS)


def lookup(url: str, evidence: list[EvidenceItem] | None = None) -> ReputationResult:
    """Resolve one URL against service-supplied evidence, then the demo feed."""
    domain = domain_of(url)
    subject = domain or url

    for item in evidence or []:
        item_domain = domain_of(item.subject) or item.subject.lower()
        if item_domain and (item_domain == domain or item_domain in url.lower()):
            boost = f" (confidence {item.confidence:.2f})" if item.confidence is not None else ""
            return ReputationResult(
                subject=subject,
                verdict=item.verdict,
                detail=(item.detail or "Reported by the service layer.") + boost,
                source=item.source,
                confidence=item.confidence if item.confidence is not None else 0.6,
                notes=["evidence supplied by service"],
            )

    if domain in _DEMO_FEED:
        verdict, detail = _DEMO_FEED[domain]
        return ReputationResult(
            subject=subject,
            verdict=verdict,
            detail=detail,
            source="demo-feed",
            confidence=0.7 if verdict == "reported" else 0.3,
        )

    if _is_official(domain):
        return ReputationResult(
            subject=subject,
            verdict="official",
            detail="Domain matches a known official host pattern.",
            source="demo-feed",
            confidence=0.6,
        )

    return ReputationResult(
        subject=subject,
        verdict="unknown",
        detail="No record in the demo feed. Unknown is not the same as safe.",
        source="demo-feed",
        confidence=0.2,
    )


def summarize(results: list[ReputationResult]) -> str:
    if not results:
        return "No link was included in the message."
    return "; ".join(f"{r.subject}: {r.verdict}" for r in results)


_DOMAIN_RE = re.compile(
    r"(?<![\w@.])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|my|net|org|top|xyz|shop|info|link|site|online|co|io|app|info)"
    r"(?:/[^\s<>\"')\]]*)?)",
    re.I,
)
_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.I)


def extract_links(text: str) -> list[str]:
    """Pull links out of free text, including bare domains, without matching emails."""
    found: list[str] = []
    spans: list[tuple[int, int]] = []
    for match in _URL_RE.finditer(text):
        found.append(match.group(0))
        spans.append(match.span())
    for match in _DOMAIN_RE.finditer(text):
        if any(start <= match.start() < end for start, end in spans):
            continue
        token = match.group(1)
        if token.lower().startswith("www."):
            token = token[4:]
        if token not in found:
            found.append(token)
    cleaned = [link.strip().rstrip(".,;:!?") for link in found]
    return [link for link in dict.fromkeys(cleaned) if link]
