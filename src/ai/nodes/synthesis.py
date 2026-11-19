"""Synthesis: deterministic composition first, model wording second, guardrails last.

The route back to a known number, the list of checks, and the recovery procedure
are computed from the request, never invented by the model. A model may improve
the wording and may raise the verdict, never lower it.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from ..llm import structured_call
from ..schemas import (
    Assessment,
    AssessmentRequest,
    CheckResult,
    CheckStatus,
    Choice,
    CompanionHint,
    CritiqueIssue,
    Finding,
    IncidentProfile,
    RiskLevel,
    TrustedContact,
    VerificationStep,
)
from ..state import WatchdogState, trace_event
from ..tools.perimeter import match_contact

GUARDRAIL_NOTE = (
    "Practice build with sample data. This flags reasons to pause; it cannot prove who "
    "sent a message or that a link is safe. The decision stays with the person."
)

_OFFICIAL_NOTE = (
    "No live official source (PDRM or bank) is connected, so nothing here is an official "
    "clearance."
)

_BANNED = [
    (re.compile(r"\bis (?:a |an )?(?:scam|fraud)\b", re.I), "shows scam-like pressure"),
    (re.compile(r"\bconfirmed scam\b", re.I), "shows several scam-like signals"),
    (re.compile(r"\bdefinitely (?:fake|fraudulent)\b", re.I), "cannot be confirmed as genuine"),
    (re.compile(r"\bproven\b", re.I), "supported by the visible clues"),
    (re.compile(r"\bguaranteed?\b", re.I), "not guaranteed"),
    (re.compile(r"\b100% safe\b", re.I), "not confirmed safe"),
    (re.compile(r"\b(?:totally |completely )?safe to pay\b", re.I), "unverified for payment"),
    (re.compile(r"\b(?:we|i) verified\b", re.I), "could not be independently verified"),
]


class AssessmentDraft(BaseModel):
    """The only free-text the synthesis model may contribute."""

    verdict: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    headline: str = Field(description="One sentence, under 16 words, spoken plainly.")
    reasons: list[str] = Field(description="Up to 5 observable reasons, one short sentence each.")
    unknown: list[str] = Field(description="What could not be verified, one short sentence each.")
    recommended_actions: list[str] = Field(description="Up to 4 concrete next steps.")


SYNTH_SYSTEM = (
    "You are the synthesis agent in a scam-prevention swarm for older Malaysians. "
    "Explain the supplied evidence in plain language. Never claim a person's identity is "
    "confirmed. Never call a link safe or malicious with certainty. Never ask the user to "
    "reply inside the suspicious conversation. Keep every sentence under 20 words. "
    "The verification route, checks and recovery steps are fixed elsewhere; do not restate "
    "them as certainties about the sender."
)


def _clean(text: str) -> str:
    cleaned = text
    for pattern, replacement in _BANNED:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned.strip()


def _clean_list(items: list[str], limit: int) -> list[str]:
    return [cleaned for cleaned in (_clean(item) for item in items) if cleaned][:limit]


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _contact(request: AssessmentRequest, profile: IncidentProfile) -> TrustedContact | None:
    return match_contact(
        handle=request.incident.sender_handle,
        display_name=request.incident.sender_display_name,
        perimeter=request.incident.perimeter,
    )


def _headline(verdict: RiskLevel, profile: IncidentProfile, name: str) -> str:
    familiar = bool(profile.sender_known or profile.matched_contact)
    if verdict is RiskLevel.high and familiar:
        return f"{name} is familiar, but this request is not. Pause before you pay."
    if verdict is RiskLevel.high:
        return "This sender is not in your trusted circle. Do not act on it."
    if verdict is RiskLevel.elevated:
        return "Something here sits outside your usual pattern. Check it another way first."
    return "Nothing here breaks your usual pattern, but stay alert."


def _unknown(request: AssessmentRequest, profile: IncidentProfile, name: str) -> list[str]:
    incident = request.incident
    items: list[str] = []
    if profile.sender_known and profile.known_route:
        items.append(
            f"The number matches your saved contact, but we cannot confirm that {name} "
            "sent this particular message."
        )
    elif profile.matched_contact:
        items.append(
            f"The name looks like {name}, but the route in this message is not one you saved."
        )
    else:
        items.append(f"We could not match this sender to anyone you trust ({name}).")

    if profile.channel.value == "call":
        items.append(
            "We cannot verify who is speaking. A voice can be copied from a short recording."
        )
    if profile.links:
        items.append(
            "We cannot confirm who owns the link. 'Not reported' is not the same as safe."
        )
    items.append(_OFFICIAL_NOTE)
    return items


def _verification_route(
    profile: IncidentProfile, contact: TrustedContact | None, name: str
) -> list[VerificationStep]:
    if contact and contact.known_handles:
        call_step = f"Open your own contact list and call {contact.name} on {contact.known_handles[0]}."
        why = "A number you saved yourself is not controlled by whoever sent this message."
    else:
        call_step = f"Ask another family member who can reach {name} in person to check."
        why = "With no saved number, a second person is the only independent route you have."

    steps = [
        VerificationStep(step=call_step, why=why),
        VerificationStep(
            step="Do not reply in this chat, and do not open the link to 'check' it.",
            why="Replying or clicking keeps you inside the channel the sender controls.",
        ),
        VerificationStep(
            step="Ask one private question that only your family would answer, not one this message already answered.",
            why="A scripted caller can repeat what they sent, but cannot answer something fresh.",
        ),
    ]
    if contact and contact.shares_secret_word:
        steps.append(
            VerificationStep(
                step=f"Ask for the family word you agreed with {contact.name}.",
                why="It is a backup check, not proof. Use it together with the saved number.",
            )
        )
    return steps


def _recovery_steps(findings: list[Finding]) -> list[str]:
    for finding in findings:
        if finding.agent == "recovery_advisor" and finding.clues:
            return _clean_list(finding.clues, 6)
    return []


def _choices(profile: IncidentProfile, contact: TrustedContact | None, name: str) -> list[Choice]:
    verify = Choice(
        id="verify_safely",
        label="Check through a number I already have",
        description=(
            f"Call {contact.name} on the saved number, outside this chat."
            if contact and contact.known_handles
            else f"Ask another family member to reach {name} in person."
        ),
        recommended=not profile.already_acted,
    )
    pause = Choice(
        id="pause",
        label="Pause and ask someone I trust",
        description="Show this message to a family member before you do anything.",
    )
    decline = Choice(
        id="decline",
        label="Stop this conversation",
        description="Do not reply, and do not send money or codes. Keep the message as evidence.",
    )
    if profile.already_acted:
        acted = Choice(
            id="already_acted",
            label="I already clicked or paid",
            description="See the recovery steps below and act on them in order.",
            recommended=True,
        )
        return [acted, pause, decline]
    proceed = Choice(
        id="continue_anyway",
        label="Continue anyway",
        description="The choice stays yours. If you continue, send no codes and pay nothing new.",
    )
    return [verify, pause, decline, proceed]


def _companion_hint(verdict: RiskLevel, profile: IncidentProfile) -> CompanionHint:
    if verdict is RiskLevel.high:
        return CompanionHint(light="red", pattern="double_pulse", phrase="Stop. Check first.")
    if verdict is RiskLevel.elevated:
        return CompanionHint(light="amber", pattern="slow_pulse", phrase="Wait. Check first.")
    return CompanionHint(light="green", pattern="steady", phrase="Looks usual.")


def _dedupe_checks(checks: list[CheckResult]) -> list[CheckResult]:
    seen: dict[str, CheckResult] = {}
    for check in checks:
        seen.setdefault(check.id, check)
    return list(seen.values())


def compose_assessment(
    request: AssessmentRequest,
    profile: IncidentProfile,
    findings: list[Finding],
    checks: list[CheckResult],
) -> Assessment:
    """Build the deterministic answer the swarm must always be able to produce."""
    verdict = RiskLevel.strongest(profile.baseline_band, *[finding.severity for finding in findings])
    contact = _contact(request, profile)
    name = profile.sender_display_name or (contact.name if contact else "this sender")

    reasons = list(profile.notes)
    for finding in findings:
        reasons.extend(finding.clues)
    reasons = _dedupe(reasons)[:6]

    actions = [
        "Pause now: do not transfer money or share codes while you feel rushed.",
        (
            f"Call {contact.name} on the number you saved ({contact.known_handles[0]}), not on this chat."
            if contact and contact.known_handles
            else f"Reach {name} through a person or route that this message does not control."
        ),
        "Keep the message, the number and any receipt. Do not delete them yet.",
    ]
    if profile.money_requested:
        actions.append("If money already left, call your bank and NSRC 997 as soon as you can.")

    checks = _dedupe_checks(checks)
    return Assessment(
        verdict=verdict,
        confidence=round(min(0.85, 0.5 + 0.04 * len(reasons) + (0.05 if profile.links else 0.0)), 2),
        headline=_headline(verdict, profile, name),
        familiar_but_unverified=bool(
            profile.matched_contact and (profile.unfamiliar_links or profile.money_requested)
        ),
        reasons=reasons,
        unknown=_unknown(request, profile, name),
        recommended_actions=actions[:4],
        verification_route=_verification_route(profile, contact, name),
        recovery_steps=_recovery_steps(findings),
        checks=checks,
        choices=_choices(profile, contact, name),
        companion_hint=_companion_hint(verdict, profile),
        guardrail_note=GUARDRAIL_NOTE,
        sources=_dedupe(["visible message text", *[check.source for check in checks]]),
        engine="rules",
    )


def _synth_human(
    request: AssessmentRequest,
    profile: IncidentProfile,
    findings: list[Finding],
    checks: list[CheckResult],
    issues: list[CritiqueIssue],
) -> str:
    payload = {
        "verdict_floor": profile.baseline_band.value,
        "profile": profile.model_dump(mode="json"),
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "checks": [check.model_dump(mode="json") for check in checks],
        "critique": [issue.model_dump(mode="json") for issue in issues],
    }
    message = request.incident.message_text
    return (
        "Message from the user's device:\n<<<\n"
        f"{message}\n"
        ">>>\n"
        f"Collected evidence: {payload}\n"
        "Write the headline, reasons, unknowns and next steps for the person. "
        "Do not go below the verdict floor."
    )


def _merge_llm(base: Assessment, draft: AssessmentDraft) -> Assessment:
    reasons = _dedupe([*_clean_list(draft.reasons, 4), *base.reasons])[:6]
    return base.model_copy(
        update={
            "verdict": RiskLevel.strongest(base.verdict, RiskLevel.coerce(draft.verdict)),
            "confidence": round(
                (base.confidence + max(0.0, min(1.0, draft.confidence))) / 2,
                2,
            ),
            "headline": _clean(draft.headline)[:160] or base.headline,
            "reasons": reasons,
            "unknown": _dedupe([*_clean_list(draft.unknown, 4), *base.unknown])[:5],
            "recommended_actions": _clean_list(draft.recommended_actions, 4) or base.recommended_actions,
            "engine": "llm+rules",
        }
    )


def enforce(
    working: Assessment,
    clean: Assessment,
    issues: list[CritiqueIssue],
) -> Assessment:
    """Re-attach the deterministic scaffolding and fix whatever the judge complained about."""
    codes = {issue.code for issue in issues}
    update: dict = {
        "verdict": RiskLevel.strongest(working.verdict, clean.verdict),
        "checks": clean.checks,
        "choices": clean.choices,
        "companion_hint": clean.companion_hint,
        "guardrail_note": clean.guardrail_note,
        "sources": _dedupe([*clean.sources, *working.sources]),
        "headline": _clean(working.headline),
        "reasons": _clean_list(working.reasons, 6),
        "unknown": _clean_list(working.unknown, 5),
        "recommended_actions": _clean_list(working.recommended_actions, 4),
        "verification_route": working.verification_route or clean.verification_route,
        "recovery_steps": working.recovery_steps or clean.recovery_steps,
    }

    if "missing_uncertainty" in codes or len(update["unknown"]) < 1:
        update["unknown"] = clean.unknown
    if "missing_route" in codes or len(working.verification_route) < 2:
        update["verification_route"] = clean.verification_route
    if "missing_recovery" in codes or (clean.recovery_steps and not working.recovery_steps):
        update["recovery_steps"] = clean.recovery_steps
    if "thin_reasons" in codes or len(update["reasons"]) < 2:
        update["reasons"] = clean.reasons

    update["confidence"] = round(max(0.0, min(0.95, working.confidence)), 2)
    return working.model_copy(update=update)


def synthesis_node(state: WatchdogState) -> dict:
    request = state["request"]
    profile = state["profile"]
    findings = state.get("findings", [])
    checks = state.get("checks", [])
    issues = state.get("critique", []) or []
    attempt = state.get("attempts", 0) + 1

    clean = compose_assessment(request, profile, findings, checks)
    working = clean
    engine = "rules"
    error: str | None = None

    if attempt == 1 and state["llm_mode"] != "offline":
        draft, error = structured_call(
            AssessmentDraft,
            system=SYNTH_SYSTEM,
            human=_synth_human(request, profile, findings, checks, issues),
            mode=state["llm_mode"],
        )
        if draft is not None:
            working = _merge_llm(clean, draft)
            engine = working.engine
    elif attempt > 1 and state.get("draft") is not None:
        working = state["draft"]
        engine = working.engine
        error = "repair_pass"

    final = enforce(working, clean, issues).model_copy(update={"engine": engine})

    events = [
        trace_event(
            "synthesis",
            f"Attempt {attempt}: {final.verdict.value} verdict ({engine}).",
            attempt=attempt,
            engine=engine,
            verdict=final.verdict.value,
            checks=[check.id for check in final.checks],
        )
    ]
    if error and error not in {"llm_disabled", "repair_pass"}:
        events.append(trace_event("synthesis", "Synthesis fell back to the rules draft.", error=error))

    return {"draft": final, "attempts": attempt, "events": events}
