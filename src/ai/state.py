"""Shared swarm state for the LangGraph loop."""

from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Annotated, TypedDict

from .schemas import (
    Assessment,
    AssessmentRequest,
    CheckResult,
    CritiqueIssue,
    Finding,
    IncidentProfile,
    RubricVerdict,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def trace_event(stage: str, message: str, **data: object) -> dict:
    """One observable step, surfaced to ``service``/``ui`` as proof of work."""
    event = {"stage": stage, "message": message, "at": now_iso()}
    event.update({key: value for key, value in data.items() if value is not None})
    return event


class SpecialistTask(TypedDict):
    agent: str
    objective: str


class WatchdogState(TypedDict, total=False):
    request: AssessmentRequest
    llm_mode: str
    started_at: float
    profile: IncidentProfile
    plan: list[str]
    task: SpecialistTask
    findings: Annotated[list[Finding], operator.add]
    checks: Annotated[list[CheckResult], operator.add]
    draft: Assessment | None
    critique: list[CritiqueIssue]
    judge: RubricVerdict | None
    assessment: Assessment | None
    attempts: int
    events: Annotated[list[dict], operator.add]
