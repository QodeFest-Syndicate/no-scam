from src.service.domain import rules
from src.service.domain.types import MessageIn

SCAM_TEXT = (
    "Hi Mak, it's me Amir. I need your help urgently! My bank account has a "
    "problem and I need to pay RM500 right now. Please use this link to help "
    "me: https://urgent-family-pay.example Please don't call me, I'm in a "
    "meeting. Just do it quickly!"
)


def make_message(text: str, sender: str = "Amir (Son)", familiar: bool = True) -> MessageIn:
    return MessageIn(sender=sender, familiar_contact=familiar, text=text)


def test_scam_sample_returns_all_four_signals_in_order():
    signals = rules.find_signals(SCAM_TEXT)
    assert [signal.id for signal in signals] == ["urgency", "link", "money", "secrecy"]


def test_malay_urgency_word_is_detected():
    assert [signal.id for signal in rules.find_signals("Tolong segera, saya perlukan bantuan.")] == [
        "urgency"
    ]


def test_benign_message_has_no_signals():
    message = make_message("Hi Mak, see you at 3pm. Call me later.")
    assessment = rules.assess_with_rules(message)
    assert assessment.level == "no_signals"
    assert assessment.signals == []
    assert "not proof" in assessment.summary


def test_single_money_request_is_flagged():
    assessment = rules.assess_with_rules(make_message("Can you transfer RM50 to me?"))
    assert assessment.level == "pause"
    assert [signal.id for signal in assessment.signals] == ["money"]


def test_familiar_contact_summary_keeps_familiar_and_unverified_distinct():
    assessment = rules.assess_with_rules(make_message(SCAM_TEXT))
    assert "familiar" in assessment.summary
    assert "not verified" in assessment.summary
    assert assessment.engine == "rules"
    assert assessment.ai_available is False


def test_checks_report_link_inspection_as_unavailable():
    assessment = rules.assess_with_rules(make_message(SCAM_TEXT))
    checks = {check.id: check for check in assessment.checks}
    assert checks["link"].status == "unavailable"
    assert checks["text_signals"].status == "completed"
    assert checks["contact"].status == "not_run"
    assert "Do not use contact details" in checks["contact"].result


def test_benign_message_link_check_is_not_run():
    assessment = rules.assess_with_rules(make_message("No links today, just a chat."))
    checks = {check.id: check for check in assessment.checks}
    assert checks["link"].status == "not_run"


def test_disclaimer_is_always_uncertainty_aware():
    assert "not proof" in rules.DISCLAIMER
    assert "have not verified" in rules.DISCLAIMER
