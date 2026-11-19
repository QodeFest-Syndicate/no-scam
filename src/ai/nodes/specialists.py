"""Parallel specialists: each owns one question and at most one check.

Deterministic rules always produce a finding first. The model may re-word it and
may raise the severity, but never lower the rule-based floor. If the gateway is
slow or down, the swarm still returns a complete, honest answer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..llm import structured_call
from ..schemas import (
    CheckResult,
    CheckStatus,
    Finding,
    IncidentProfile,
    RiskLevel,
)
from ..state import WatchdogState, trace_event
from ..tools.perimeter import match_contact, route_is_known
from ..tools.reputation import lookup

SYSTEM = (
    "You support a scam-prevention assistant used by older Malaysians and their families. "
    "Use only the supplied text and tool results. Describe observable clues, never certainty "
    "about who someone is or what they intend. Never claim a link is safe or malicious with "
    "certainty. Keep every sentence under 22 words, in plain language."
)


class FindingDraft(BaseModel):
    """What a specialist model is allowed to return."""

    severity: RiskLevel = RiskLevel.elevated
    summary: str = Field(description="At most two sentences.")
    clues: list[str] = Field(default_factory=list, description="At most four observable clues.")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


def _llm_draft(
    agent: str,
    objective: str,
    state: WatchdogState,
    extras: str = "",
) -> tuple[FindingDraft | None, str | None]:
    request = state["request"]
    profile = state["profile"]
    human = (
        f"Agent: {agent}\n"
        f"Objective: {objective}\n"
        f"Channel: {profile.channel.value}\n"
        f'Message text:\n"""\n{request.incident.message_text}\n"""\n'
        f"Derived profile: {profile.model_dump_json()}\n"
        f"{extras}\n"
        "Return severity, a two-sentence summary, up to four observable clues, and confidence."
    )
    return structured_call(FindingDraft, system=SYSTEM, human=human, mode=state["llm_mode"])


def _merge(base: Finding, draft: FindingDraft | None) -> Finding:
    if draft is None:
        return base
    clues = [clue.strip() for clue in draft.clues if clue and clue.strip()][:4]
    confidence = round((base.confidence + max(0.0, min(1.0, draft.confidence))) / 2, 2)
    return base.model_copy(
        update={
            "severity": RiskLevel.strongest(base.severity, RiskLevel.coerce(draft.severity)),
            "summary": (draft.summary or "").strip() or base.summary,
            "clues": clues or base.clues,
            "confidence": confidence,
            "source": "llm+rules",
        }
    )


def _pattern_names(profile: IncidentProfile) -> list[str]:
    names: list[str] = []
    if profile.urgency_hits:
        names.append("time pressure")
    if profile.secrecy_hits:
        names.append("a request for secrecy")
    if profile.money_requested:
        names.append("a money request")
    if profile.claims_new_number:
        names.append("a claimed new number")
    if profile.credential_hits:
        names.append("a request for codes or passwords")
    if profile.authority_hits:
        names.append("an authority claim")
    if profile.unfamiliar_links:
        names.append("a link outside your routine")
    return names


def _status(*, concern: bool) -> CheckStatus:
    return CheckStatus.concern if concern else CheckStatus.ok


def _signal_analyst(state: WatchdogState) -> tuple[Finding, list[CheckResult], str | None]:
    profile = state["profile"]
    patterns = _pattern_names(profile)
    if patterns:
        summary = "This message shows " + ", ".join(patterns) + "."
    else:
        summary = "Nothing in the wording itself creates pressure."
    base = Finding(
        agent="signal_analyst",
        focus="Pressure patterns in the message",
        severity=profile.baseline_band,
        summary=summary,
        clues=profile.notes[:4],
        confidence=0.7 if patterns else 0.5,
        source="rules",
    )
    check = CheckResult(
        id="pressure_patterns",
        label="Pressure patterns in the wording",
        kind="procedure",
        source="visible message text + prepared procedure (simulated)",
        status=_status(concern=bool(patterns)),
        result=summary,
        simulated=True,
        evidence=patterns,
    )
    draft, error = _llm_draft("signal_analyst", state["task"]["objective"], state)
    finding = _merge(base, draft)
    return finding, [check], error


def _perimeter_analyst(state: WatchdogState) -> tuple[Finding, list[CheckResult], str | None]:
    request = state["request"]
    profile = state["profile"]
    contact = match_contact(
        handle=request.incident.sender_handle,
        display_name=request.incident.sender_display_name,
        perimeter=request.incident.perimeter,
    )
    handle = profile.sender_handle or "no number shown"

    if contact and profile.sender_known and route_is_known(contact, profile.channel):
        severity = RiskLevel.low
        summary = (
            f"This came through the {profile.channel.value} route you already saved for "
            f"{contact.name}, so the sender route is familiar."
        )
        clues = [
            f"Saved route matches {handle}.",
            "A familiar route still does not verify this particular request.",
        ]
        concern = False
    elif contact:
        severity = RiskLevel.high
        saved = ", ".join(contact.known_handles) or "none saved"
        summary = (
            f"The name matches {contact.name}, but the number in this message is not one "
            "you saved."
        )
        clues = [
            f"This message uses {handle}.",
            f"Your saved number for {contact.name}: {saved}.",
            "A familiar display name can be copied or an account taken over.",
        ]
        concern = True
    else:
        severity = RiskLevel.high
        summary = "This sender is not in your saved contacts at all."
        clues = [
            f"This message uses {handle}.",
            "No saved contact matches this name or number.",
        ]
        concern = True

    base = Finding(
        agent="perimeter_analyst",
        focus="Claimed identity vs. saved routes",
        severity=severity,
        summary=summary,
        clues=clues,
        confidence=0.8 if concern else 0.65,
        source="rules",
    )
    check = CheckResult(
        id="sender_route",
        label="Sender number against your saved contacts",
        kind="perimeter_route",
        source="your saved contacts",
        status=_status(concern=concern),
        result=summary,
        simulated=False,
        evidence=clues,
    )
    draft, error = _llm_draft(
        "perimeter_analyst",
        state["task"]["objective"],
        state,
        extras=f"Saved contact match: {contact.name if contact else 'none'}",
    )
    return _merge(base, draft), [check], error


def _link_inspector(state: WatchdogState) -> tuple[Finding, list[CheckResult]]:
    request = state["request"]
    profile = state["profile"]
    evidence = request.incident.evidence

    if not profile.links:
        base = Finding(
            agent="link_inspector",
            focus="Link reputation",
            severity=RiskLevel.low,
            summary="No link was included, so no link check was needed.",
            clues=[],
            confidence=0.9,
            source="rules",
        )
        return base, []

    results = [(link, lookup(link, evidence)) for link in profile.links]
    severity_map = {
        "reported": RiskLevel.high,
        "not_found": RiskLevel.elevated,
        "unknown": RiskLevel.elevated,
        "official": RiskLevel.low,
    }
    severities = [severity_map.get(result.verdict, RiskLevel.elevated) for _, result in results]
    severity = RiskLevel.strongest(*severities)

    clues = [f"{result.subject}: {result.verdict}. {result.detail}" for _, result in results]
    checks: list[CheckResult] = []
    for _, result in results:
        demo = result.source == "demo-feed"
        checks.append(
            CheckResult(
                id=f"link:{result.subject}",
                label=f"Report lookup for {result.subject}",
                kind="link_reputation",
                source="local demo report feed (simulated)" if demo else result.source,
                status=_status(concern=result.verdict != "official"),
                result=result.detail,
                simulated=demo,
                evidence=[f"verdict={result.verdict}", f"confidence={result.confidence:.2f}"],
            )
        )

    if any(result.verdict == "reported" for _, result in results):
        summary = (
            "At least one link appears in the demo report feed. That is a reason to stop, "
            "not proof of who sent it."
        )
    else:
        summary = (
            "The link has no confirmed report, which does not make it safe. "
            "Its owner stays unverified."
        )

    base = Finding(
        agent="link_inspector",
        focus="Link reputation",
        severity=severity,
        summary=summary,
        clues=clues[:4],
        confidence=0.75,
        source="tool:reputation",
    )
    return base, checks


def _recovery_advisor(state: WatchdogState) -> tuple[Finding, list[CheckResult], str | None]:
    steps = [
        "Stop here. Do not send more money, fees, codes, or documents from this conversation.",
        "Call your bank's official number from your card or app and ask them to hold the transfer.",
        "Call the National Scam Response Centre on 997 and note the time, amount and reference.",
        "Tell one family member now. The request for secrecy is part of the trap, not kindness.",
        "Change passwords only inside the official app, never through a link in a message.",
    ]
    summary = (
        "You told us you already acted. These steps limit the damage; acting on them early "
        "matters more than anything else on this screen."
    )
    base = Finding(
        agent="recovery_advisor",
        focus="Next steps after acting",
        severity=RiskLevel.high,
        summary=summary,
        clues=steps,
        confidence=0.8,
        source="rules",
    )
    check = CheckResult(
        id="recovery_guidance",
        label="Prepared recovery procedure",
        kind="procedure",
        source="prepared demo guidance (simulated, not legal advice)",
        status=CheckStatus.concern,
        result="Recovery steps were produced from the prepared procedure for 'already acted'.",
        simulated=True,
        evidence=["bank hotline", "NSRC 997"],
    )
    draft, error = _llm_draft("recovery_advisor", state["task"]["objective"], state)
    return _merge(base, draft), [check], error


def specialist_node(state: WatchdogState) -> dict:
    agent = state["task"]["agent"]
    error: str | None = None

    if agent == "signal_analyst":
        finding, checks, error = _signal_analyst(state)
    elif agent == "perimeter_analyst":
        finding, checks, error = _perimeter_analyst(state)
    elif agent == "link_inspector":
        finding, checks = _link_inspector(state)
    elif agent == "recovery_advisor":
        finding, checks, error = _recovery_advisor(state)
    else:  # defensive: an unknown agent must not break the swarm
        finding = Finding(
            agent=agent,
            focus="Unknown specialist",
            summary="This specialist was not recognised, so it contributed nothing.",
            confidence=0.0,
        )
        checks = []

    events = [
        trace_event(
            "specialist",
            f"{agent}: {finding.summary}",
            agent=agent,
            severity=finding.severity.value,
            source=finding.source,
        )
    ]
    if error and error not in {"llm_disabled"}:
        events.append(trace_event("specialist", f"{agent} fell back to rules.", agent=agent, error=error))

    return {"findings": [finding], "checks": checks, "events": events}
