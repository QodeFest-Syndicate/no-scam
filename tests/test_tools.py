"""Deterministic tooling: clue extraction, perimeter matching, link parsing."""

from __future__ import annotations

from ai.fixtures import load_case
from ai.schemas import RiskLevel
from ai.tools.perimeter import handles_match
from ai.tools.reputation import extract_links, lookup
from ai.tools.signals import analyze_incident


def test_benign_message_stays_low() -> None:
    profile = analyze_incident(load_case("benign-family-message"))
    assert profile.baseline_band is RiskLevel.low
    assert profile.sender_known is True
    assert profile.known_route is True
    assert profile.risk_score == 0


def test_impersonation_call_hits_the_floor() -> None:
    profile = analyze_incident(load_case("voice-clone-call"))
    assert profile.baseline_band is RiskLevel.high
    assert profile.claims_new_number is True
    assert profile.sender_known is False
    assert profile.money_requested is True
    assert profile.amount_myr == 4800.0
    assert profile.secrecy_hits


def test_familiar_account_can_still_be_unsafe() -> None:
    profile = analyze_incident(load_case("familiar-link"))
    assert profile.sender_known is True
    assert profile.known_route is True
    assert profile.baseline_band is RiskLevel.high
    assert any("parcel-redelivery-my.top" in link for link in profile.unfamiliar_links)


def test_handle_matching_tolerates_formatting() -> None:
    assert handles_match("+60 19-888 7766", "+60198887766")
    assert handles_match("019-888 7766", "+60 19 888 7766")
    assert not handles_match("+60 11-2233 4455", "+60 19-888 7766")


def test_links_extracted_without_emails() -> None:
    links = extract_links(
        "Mail daniel@example.com or see https://a.example-shop.top/pay and b.example.org/x"
    )
    assert "https://a.example-shop.top/pay" in links
    assert any("b.example.org" in link for link in links)
    assert all("daniel@" not in link for link in links)


def test_reputation_prefers_service_evidence() -> None:
    case = load_case("already-clicked")
    evidence = case.incident.evidence
    result = lookup("https://secure-maybank-verify.info/track", evidence)
    assert result.verdict == "reported"
    assert result.source == "service:demo-report-check"


def test_short_tokens_need_word_boundaries() -> None:
    # "contact" and "tactic" must not be read as a TAC / PIN request.
    case = load_case("benign-family-message").model_copy(deep=True)
    case.incident.message_text = "Please keep in contact. That tactic is common in advertising."
    profile = analyze_incident(case)
    assert profile.credential_hits == []
