"""Judge: the rubric gate that decides whether the draft may ship.

The rubric encodes the master brief's completion criteria: visible evidence,
honest uncertainty, an independent route, recovery support, and simulated
elements that are labelled as simulated.
"""

from __future__ import annotations

from ..schemas import Assessment, IncidentProfile, RubricCheck, RubricVerdict
from ..state import WatchdogState, trace_event

VERDICT_ORDER = {"low": 0, "elevated": 1, "high": 2}


def evaluate(assessment: Assessment, profile: IncidentProfile) -> RubricVerdict:
    checks: list[RubricCheck] = []

    complete = bool(
        assessment.headline.strip()
        and assessment.reasons
        and assessment.unknown
        and assessment.recommended_actions
    )
    checks.append(
        RubricCheck(
            name="complete_fields",
            passed=complete,
            detail="Headline, reasons, unknowns and next steps are all present."
            if complete
            else "One of headline, reasons, unknowns or next steps is empty.",
        )
    )

    body = " ".join(
        [
            assessment.headline,
            *assessment.reasons,
            *assessment.unknown,
            *assessment.recommended_actions,
            *assessment.recovery_steps,
        ]
    ).lower()
    overclaims = [
        phrase
        for phrase in ("is a scam", "confirmed scam", "definitely fake", "proven", "guaranteed", "100% safe", "safe to pay")
        if phrase in body
    ]
    checks.append(
        RubricCheck(
            name="no_overclaim",
            passed=not overclaims,
            detail="No certainty language." if not overclaims else f"Certainty language: {overclaims}.",
        )
    )

    uncertain = any(
        marker in " ".join(assessment.unknown).lower()
        for marker in ("cannot", "could not", "unverified", "uncertain", "unknown", "unresolved")
    )
    checks.append(
        RubricCheck(
            name="uncertainty_visible",
            passed=uncertain,
            detail="Unverified parts are stated." if uncertain else "No unverified statement found.",
        )
    )

    route_text = " ".join(step.step for step in assessment.verification_route).lower()
    independent = len(assessment.verification_route) >= 2 and any(
        marker in route_text for marker in ("call", "saved", "contact list", "another family", "in person")
    )
    checks.append(
        RubricCheck(
            name="independent_route",
            passed=independent,
            detail="A route outside the conversation is offered."
            if independent
            else "No independent verification route outside the conversation.",
        )
    )

    if profile.already_acted:
        recovered = len(assessment.recovery_steps) >= 3
        checks.append(
            RubricCheck(
                name="recovery_when_acted",
                passed=recovered,
                detail=f"{len(assessment.recovery_steps)} recovery step(s)."
                if recovered
                else "Already-acted path lacks ordered recovery steps.",
            )
        )

    checks.append(
        RubricCheck(
            name="cites_clues",
            passed=len(assessment.reasons) >= 2,
            detail=f"{len(assessment.reasons)} reason(s) shown.",
        )
    )

    floor_ok = VERDICT_ORDER[assessment.verdict.value] >= VERDICT_ORDER[profile.baseline_band.value]
    checks.append(
        RubricCheck(
            name="verdict_at_or_above_floor",
            passed=floor_ok,
            detail=f"Verdict {assessment.verdict.value} vs floor {profile.baseline_band.value}.",
        )
    )

    labelled = len(assessment.checks) >= 3 and all(check.source.strip() for check in assessment.checks)
    simulated_labelled = all(
        check.source.lower().find("simulat") >= 0 or check.source.lower().find("demo") >= 0
        for check in assessment.checks
        if check.simulated
    )
    checks.append(
        RubricCheck(
            name="checks_visible",
            passed=labelled,
            detail=f"{len(assessment.checks)} check(s) with a named source."
            if labelled
            else "Fewer than three checks, or a check without a source.",
        )
    )
    checks.append(
        RubricCheck(
            name="simulation_labelled",
            passed=simulated_labelled,
            detail="Every simulated check says so."
            if simulated_labelled
            else "A simulated check is not labelled as simulated.",
        )
    )

    passed_count = sum(1 for check in checks if check.passed)
    score = round(passed_count / len(checks), 2)
    failed = [check.name for check in checks if not check.passed]
    return RubricVerdict(
        passed=not failed,
        score=score,
        checks=checks,
        required_fixes=failed,
    )


def judge_node(state: WatchdogState) -> dict:
    assessment = state["draft"]
    if assessment is None:
        return {"judge": None, "events": [trace_event("judge", "No draft to judge.")]}

    verdict = evaluate(assessment, state["profile"])
    return {
        "judge": verdict,
        "events": [
            trace_event(
                "judge",
                f"Rubric {'passed' if verdict.passed else 'failed'} at {verdict.score:.2f}.",
                score=verdict.score,
                failed=verdict.required_fixes,
            )
        ],
    }
