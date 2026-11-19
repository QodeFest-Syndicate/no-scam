"""Offline swarm behaviour: verdict floors, rubric, repair loop, honest labels."""

from __future__ import annotations

from ai import assess
from ai.fixtures import list_cases, load_case
from ai.nodes.critique import review
from ai.nodes.judge import evaluate
from ai.nodes.synthesis import enforce
from ai.schemas import CritiqueIssue, RiskLevel
from ai.tools.signals import analyze_incident

STAGES = {"intake", "triage", "specialist", "synthesis", "critique", "judge", "finalize"}


def test_every_scripted_case_passes_the_rubric() -> None:
    for name, _ in list_cases():
        assessment = assess(load_case(name), mode="offline")
        assert assessment.rubric_score == 1.0, name
        assert assessment.revisions == 0, name
        assert STAGES <= {event["stage"] for event in assessment.trace}, name


def test_expected_bands() -> None:
    expectations = {
        "familiar-link": RiskLevel.high,
        "voice-clone-call": RiskLevel.high,
        "already-clicked": RiskLevel.high,
        "benign-family-message": RiskLevel.low,
    }
    for name, band in expectations.items():
        assert assess(load_case(name), mode="offline").verdict is band, name


def test_familiar_account_is_flagged_as_unverified_request() -> None:
    assessment = assess(load_case("familiar-link"), mode="offline")
    assert assessment.familiar_but_unverified is True
    assert any("saved" in reason.lower() for reason in assessment.reasons)
    assert any("cannot" in line.lower() for line in assessment.unknown)


def test_unavailable_checks_stay_visible() -> None:
    assessment = assess(load_case("familiar-link"), mode="offline")
    by_id = {check.id: check for check in assessment.checks}
    assert by_id["official_source"].status.value == "unavailable"
    assert by_id["official_source"].simulated is True
    assert "simulat" in by_id["official_source"].source.lower()
    assert by_id["contact_route"].status.value == "not_run"


def test_already_acted_gets_ordered_recovery() -> None:
    assessment = assess(load_case("already-clicked"), mode="offline")
    assert len(assessment.recovery_steps) >= 3
    assert any("997" in step for step in assessment.recovery_steps)
    assert assessment.choices[0].id == "already_acted"
    assert assessment.choices[0].recommended is True


def test_benign_case_keeps_the_person_in_motion() -> None:
    assessment = assess(load_case("benign-family-message"), mode="offline")
    assert assessment.companion_hint is not None
    assert assessment.companion_hint.light == "green"
    assert len(assessment.recovery_steps) == 0


def test_swarm_is_deterministic_offline() -> None:
    first = assess(load_case("voice-clone-call"), mode="offline")
    second = assess(load_case("voice-clone-call"), mode="offline")
    assert (first.verdict, first.headline, first.reasons) == (
        second.verdict,
        second.headline,
        second.reasons,
    )


def test_overclaim_is_caught_and_repaired() -> None:
    case = load_case("familiar-link")
    profile = analyze_incident(case)
    clean = assess(case, mode="offline")
    bad = clean.model_copy(
        update={
            "headline": "This is a scam and the link is proven malicious.",
            "verdict": RiskLevel.low,
            "recovery_steps": [],
        }
    )

    issues = review(bad, profile)
    codes = {issue.code for issue in issues}
    assert "overclaim" in codes
    assert "underclaim" in codes

    repaired = enforce(bad, clean, issues)
    assert "is a scam" not in repaired.headline.lower()
    assert repaired.verdict is RiskLevel.high
    assert repaired.checks == clean.checks
    assert evaluate(repaired, profile).passed is True


def test_missing_recovery_is_a_critique_issue() -> None:
    case = load_case("already-clicked")
    assessment = assess(case, mode="offline")
    stripped = assessment.model_copy(update={"recovery_steps": []})
    issues = review(stripped, analyze_incident(case))
    assert any(issue.code == "missing_recovery" for issue in issues)


def test_issue_schema_accepts_known_codes() -> None:
    issue = CritiqueIssue(code="thin_reasons", detail="one reason", fix="add more")
    assert issue.code == "thin_reasons"
