"""Critique: the guardrail reviewer. Deterministic by default, model-assisted on demand."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from ..llm import structured_call
from ..schemas import Assessment, CritiqueIssue, IncidentProfile
from ..state import WatchdogState, trace_event

BANNED_PHRASES = (
    "is a scam",
    "confirmed scam",
    "definitely fake",
    "proven",
    "guaranteed",
    "100% safe",
    "safe to pay",
    "we verified",
    "i verified",
    "definitely safe",
)

UNCERTAINTY_MARKERS = (
    "cannot",
    "could not",
    "not confirm",
    "unverified",
    "uncertain",
    "unresolved",
    "unknown",
    "not the same as safe",
)

ROUTE_MARKERS = (
    "call",
    "saved",
    "contact list",
    "another family",
    "official app",
    "in person",
)


class CritiqueResponse(BaseModel):
    issues: list[CritiqueIssue] = Field(default_factory=list)


CRITIC_SYSTEM = (
    "You audit a scam-prevention assessment for overclaiming. Reject any sentence that "
    "asserts identity, intent, guilt, or link safety as fact. The assessment must keep "
    "uncertainty visible and must send the person to a route outside the suspicious "
    "conversation. Return only real violations."
)


def _text(assessment: Assessment) -> str:
    parts = [
        assessment.headline,
        *assessment.reasons,
        *assessment.unknown,
        *assessment.recommended_actions,
        *assessment.recovery_steps,
    ]
    return " ".join(parts).lower()


def review(assessment: Assessment, profile: IncidentProfile) -> list[CritiqueIssue]:
    issues: list[CritiqueIssue] = []
    text = _text(assessment)

    hit = next((phrase for phrase in BANNED_PHRASES if phrase in text), None)
    if hit:
        issues.append(
            CritiqueIssue(
                code="overclaim",
                detail=f"Certainty phrase found: '{hit}'.",
                fix="Replace it with an observation about the visible clues.",
            )
        )

    unknown_text = " ".join(assessment.unknown).lower()
    if not assessment.unknown or not any(marker in unknown_text for marker in UNCERTAINTY_MARKERS):
        issues.append(
            CritiqueIssue(
                code="missing_uncertainty",
                detail="No plain-language statement of what remains unverified.",
                fix="Keep at least one 'we cannot confirm ...' sentence.",
            )
        )

    route_text = " ".join(step.step for step in assessment.verification_route).lower()
    if len(assessment.verification_route) < 2 or not any(
        marker in route_text for marker in ROUTE_MARKERS
    ):
        issues.append(
            CritiqueIssue(
                code="missing_route",
                detail="No independent verification route outside this conversation.",
                fix="Add the saved-number call and the 'do not reply here' step.",
            )
        )

    if profile.already_acted and len(assessment.recovery_steps) < 3:
        issues.append(
            CritiqueIssue(
                code="missing_recovery",
                detail="The person already acted, but recovery steps are missing or thin.",
                fix="Add the ordered recovery procedure.",
            )
        )

    if len(assessment.reasons) < 2:
        issues.append(
            CritiqueIssue(
                code="thin_reasons",
                detail="Fewer than two observable reasons are shown.",
                fix="Cite the visible clues that triggered the check.",
            )
        )

    if assessment.verdict.rank < profile.baseline_band.rank:
        issues.append(
            CritiqueIssue(
                code="underclaim",
                detail="The verdict sits below what the visible clues justify.",
                fix="Raise the verdict to the rule-based floor.",
            )
        )
    return issues


def _llm_review(assessment: Assessment, state: WatchdogState) -> tuple[list[CritiqueIssue], str | None]:
    human = (
        "Assessment under review: "
        f"{assessment.model_dump_json()}\n"
        "Guardrails: never confirm identity or intent; never certify a link; "
        "keep at least one unverified statement; route the person outside the chat."
    )
    response, error = structured_call(
        CritiqueResponse, system=CRITIC_SYSTEM, human=human, mode=state["llm_mode"]
    )
    return (response.issues if response else []), error


def critique_node(state: WatchdogState) -> dict:
    assessment = state["draft"]
    profile = state["profile"]
    if assessment is None:
        return {"critique": [], "events": [trace_event("critique", "No draft to review.")]}

    issues = review(assessment, profile)
    events = [
        trace_event(
            "critique",
            f"{len(issues)} guardrail issue(s) found.",
            codes=[issue.code for issue in issues],
        )
    ]

    if os.getenv("WATCHDOG_LLM_CRITIQUE", "0").strip().lower() in {"1", "true", "on", "yes"}:
        extra, error = _llm_review(assessment, state)
        seen = {(issue.code, issue.detail) for issue in issues}
        for issue in extra:
            if (issue.code, issue.detail) not in seen:
                issues.append(issue)
                seen.add((issue.code, issue.detail))
        if error and error != "llm_disabled":
            events.append(trace_event("critique", "Model critic unavailable; rules only.", error=error))

    return {"critique": issues, "events": events}
