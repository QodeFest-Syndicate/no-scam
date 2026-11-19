"""Wire contracts for the watchdog swarm.

Everything the ``service`` layer sends in and gets out is defined here. The
swarm never talks about frameworks outside this module, so ``service`` can
depend on the JSON shape without depending on LangGraph internals.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_HIGH = re.compile(r"\b(high|critical|severe|dangerous|tinggi)\b", re.I)
_ELEVATED = re.compile(r"\b(elevated|medium|moderate|caution|sedang)\b", re.I)
_LOW = re.compile(r"\b(low|none|minimal|rendah)\b", re.I)


class RiskLevel(str, Enum):
    """Three-band verdict. Deliberately coarse: this is a pause signal, not a diagnosis."""

    low = "low"
    elevated = "elevated"
    high = "high"

    @classmethod
    def coerce(cls, value: object) -> "RiskLevel":
        """Map free-form model text (``"Very High"``, ``"Medium"``) onto a band."""
        if isinstance(value, cls):
            return value
        text = str(value or "").strip()
        if text.lower() in {member.value for member in cls}:
            return cls(text.lower())
        if _HIGH.search(text):
            return cls.high
        if _ELEVATED.search(text):
            return cls.elevated
        if _LOW.search(text):
            return cls.low
        return cls.elevated

    @property
    def rank(self) -> int:
        return {"low": 0, "elevated": 1, "high": 2}[self.value]

    @classmethod
    def strongest(cls, *levels: "RiskLevel") -> "RiskLevel":
        return max(levels, key=lambda level: level.rank) if levels else cls.low


class Channel(str, Enum):
    whatsapp = "whatsapp"
    sms = "sms"
    call = "call"
    email = "email"
    social = "social"
    marketplace = "marketplace"
    unknown = "unknown"


class TrustedContact(BaseModel):
    """One entry of the user's trusted perimeter."""

    model_config = ConfigDict(extra="ignore")

    name: str
    relationship: str | None = None
    known_handles: list[str] = Field(default_factory=list)
    known_channels: list[Channel] = Field(default_factory=list)
    known_link_domains: list[str] = Field(
        default_factory=list, description="Domains this contact routinely shares, e.g. a courier portal."
    )
    shares_secret_word: bool = False
    note: str | None = None


class EvidenceItem(BaseModel):
    """Pre-fetched evidence handed over by ``service`` (typically via ``mcp``).

    The swarm treats these as *claims with provenance*, never as verified truth.
    """

    model_config = ConfigDict(extra="ignore")

    subject: str
    verdict: Literal["official", "reported", "not_found", "unknown"] = "unknown"
    source: str = "service"
    detail: str | None = None
    confidence: float | None = None


class IncidentRequest(BaseModel):
    """The moment being assessed: one message, call, or link from a familiar-looking source."""

    model_config = ConfigDict(extra="ignore")

    message_text: str = Field(min_length=1)
    channel: Channel = Channel.unknown
    sender_display_name: str | None = None
    sender_handle: str | None = None
    links: list[str] = Field(default_factory=list)
    amount_myr: float | None = None
    already_acted: bool = False
    acted_details: str | None = None
    perimeter: list[TrustedContact] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    language: str = "en"


class AssessmentRequest(BaseModel):
    """Envelope consumed by ``watchdog_ai.api.assess``."""

    model_config = ConfigDict(extra="ignore")

    incident: IncidentRequest
    user_label: str | None = Field(
        default=None, description="How to address the person, e.g. 'Puan Salmah'."
    )
    mode: Literal["auto", "llm", "offline"] = "auto"
    max_revisions: int = Field(default=1, ge=0, le=3)


class IncidentProfile(BaseModel):
    """Deterministic reading of the incident before any model is consulted."""

    model_config = ConfigDict(extra="ignore")

    channel: Channel
    sender_handle: str | None = None
    sender_display_name: str | None = None
    matched_contact: str | None = None
    sender_known: bool = False
    known_route: bool = False
    claims_new_number: bool = False
    links: list[str] = Field(default_factory=list)
    unfamiliar_links: list[str] = Field(default_factory=list)
    amount_myr: float | None = None
    money_requested: bool = False
    urgency_hits: list[str] = Field(default_factory=list)
    secrecy_hits: list[str] = Field(default_factory=list)
    authority_hits: list[str] = Field(default_factory=list)
    credential_hits: list[str] = Field(default_factory=list)
    new_number_hits: list[str] = Field(default_factory=list)
    already_acted: bool = False
    risk_score: int = 0
    baseline_band: RiskLevel = RiskLevel.low
    notes: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    """One specialist's contribution, merged back into the shared swarm state."""

    model_config = ConfigDict(extra="ignore")

    agent: str
    focus: str
    severity: RiskLevel = RiskLevel.elevated
    summary: str
    clues: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = "rules"
    evidence: list[str] = Field(default_factory=list)


class VerificationStep(BaseModel):
    model_config = ConfigDict(extra="ignore")

    step: str
    why: str


class CheckStatus(str, Enum):
    """Result of one named check, so ``ui`` can show checked / unresolved / unavailable."""

    ok = "ok"
    concern = "concern"
    unresolved = "unresolved"
    unavailable = "unavailable"
    not_run = "not_run"


class CheckResult(BaseModel):
    """Evidence-bearing check with provenance. Simulated checks must stay labelled."""

    model_config = ConfigDict(extra="ignore")

    id: str
    label: str
    kind: Literal["perimeter_route", "link_reputation", "official_source", "contact_route", "procedure"]
    source: str
    status: CheckStatus
    result: str
    simulated: bool = True
    evidence: list[str] = Field(default_factory=list)


class CompanionHint(BaseModel):
    """Minimal payload for the physical companion (light pattern + short phrase)."""

    model_config = ConfigDict(extra="ignore")

    light: Literal["green", "amber", "red"]
    pattern: Literal["steady", "slow_pulse", "double_pulse"]
    phrase: str


class Choice(BaseModel):
    """The decision the person keeps control of."""

    model_config = ConfigDict(extra="ignore")

    id: Literal["verify_safely", "pause", "decline", "continue_anyway", "already_acted"]
    label: str
    description: str
    recommended: bool = False


class CritiqueIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: Literal[
        "overclaim",
        "missing_uncertainty",
        "missing_route",
        "missing_recovery",
        "thin_reasons",
        "underclaim",
    ]
    detail: str
    fix: str


class Assessment(BaseModel):
    """What ``service`` renders to the UI and what the judge rubric scores."""

    model_config = ConfigDict(extra="ignore")

    verdict: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    headline: str
    familiar_but_unverified: bool = False
    reasons: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    verification_route: list[VerificationStep] = Field(default_factory=list)
    recovery_steps: list[str] = Field(default_factory=list)
    checks: list[CheckResult] = Field(default_factory=list)
    choices: list[Choice] = Field(default_factory=list)
    companion_hint: CompanionHint | None = None
    guardrail_note: str = Field(default="")
    sources: list[str] = Field(default_factory=list)
    engine: str = "rules"
    revisions: int = 0
    rubric_score: float = 0.0
    elapsed_ms: int = 0
    trace: list[dict] = Field(default_factory=list)


class RubricCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    passed: bool
    detail: str


class RubricVerdict(BaseModel):
    model_config = ConfigDict(extra="ignore")

    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    checks: list[RubricCheck] = Field(default_factory=list)
    required_fixes: list[str] = Field(default_factory=list)
