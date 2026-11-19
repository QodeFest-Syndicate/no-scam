"""Calm, general next steps after someone has already acted.

Content stays general per the demo boundary: no promises of recovery, no
claims that an account is secure, and official contact routes only.
"""

from __future__ import annotations

from .types import Incident, RecoveryResponse, RecoveryStep

RECOVERY_DISCLAIMER = (
    "These are general next steps for this demo. They do not guarantee "
    "recovery or account security. For money already sent, call your bank "
    "using the number on your card or statement and the National Scam "
    "Response Centre (NSRC) on 997. Use official contact details you already "
    "trust — never the ones in the suspicious message."
)

_STEPS: dict[Incident, list[tuple[str, str, bool]]] = {
    "clicked_link": [
        (
            "Stop interacting with the page",
            "Close the page. Do not enter information, download files or install "
            "anything from it.",
            True,
        ),
        (
            "Check what you entered",
            "If you typed a password, card number or one-time code, follow the "
            "steps for information or credentials you shared.",
            False,
        ),
        (
            "Report the message",
            "Report it to the app or platform where you received it so they can "
            "review the link.",
            False,
        ),
        (
            "Tell someone you trust",
            "Ask a family member or friend to help you check your accounts and "
            "keep you company while you do it.",
            False,
        ),
    ],
    "entered_credentials": [
        (
            "Change the password now",
            "Use the official app or website you normally open — not the link in "
            "the message. Set a new password you have not used elsewhere.",
            True,
        ),
        (
            "Turn on two-step verification",
            "If the service offers it, add a second step such as an app code or "
            "SMS code.",
            False,
        ),
        (
            "Call your bank",
            "If you entered banking, card or one-time code details, call the "
            "number on your card or statement and explain what happened.",
            True,
        ),
        (
            "Watch for unusual activity",
            "Review recent logins and payments. Report anything you do not "
            "recognise to the service and your bank.",
            False,
        ),
        (
            "Tell someone you trust",
            "Ask a family member or friend to help you check the accounts and "
            "watch for follow-up messages.",
            False,
        ),
    ],
    "sent_money": [
        (
            "Call your bank immediately",
            "Use the official number on your card or statement. Ask whether the "
            "transfer can be stopped or recalled.",
            True,
        ),
        (
            "Report to NSRC on 997",
            "The National Scam Response Centre can help coordinate with banks and "
            "the police.",
            True,
        ),
        (
            "Make a police report",
            "Bring the message, transaction details and any screenshots.",
            False,
        ),
        (
            "Keep the evidence",
            "Save screenshots of the message, the link, the account details and "
            "the payment confirmation.",
            False,
        ),
        (
            "Stop further payments",
            "Do not send more money. Be alert to people who offer to recover your "
            "money for a fee — that can be a second scam.",
            False,
        ),
    ],
    "shared_info": [
        (
            "Change passwords for affected accounts",
            "Start with the accounts connected to the information you shared, and "
            "use the official app or website.",
            True,
        ),
        (
            "Turn on two-step verification",
            "Add a second step such as an app code or SMS code where it is "
            "available.",
            False,
        ),
        (
            "Tell your bank",
            "If you shared financial or identity details, call the number on your "
            "card or statement and ask what to watch for.",
            True,
        ),
        (
            "Watch for unusual messages and logins",
            "Scammers may use what they learned to try again. Pause and verify "
            "through a known route.",
            False,
        ),
        (
            "Tell someone you trust",
            "Ask a family member or friend to help you check the accounts.",
            False,
        ),
    ],
}


def get_recovery(incident: str) -> RecoveryResponse:
    if incident not in _STEPS:
        raise ValueError(f"Unknown incident: {incident}")
    steps = [
        RecoveryStep(order=index, title=title, detail=detail, urgent=urgent)
        for index, (title, detail, urgent) in enumerate(_STEPS[incident], start=1)
    ]
    return RecoveryResponse(
        incident=incident,
        steps=steps,
        disclaimer=RECOVERY_DISCLAIMER,
    )
