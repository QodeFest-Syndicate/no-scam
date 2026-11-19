"""One scripted demo scenario. Sample data only — no real people or links."""

from __future__ import annotations

from .types import MessageIn, Scenario

SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        id="amir-payment",
        label="Urgent payment request from a familiar family account",
        message=MessageIn(
            sender="Amir (Son)",
            familiar_contact=True,
            channel="whatsapp",
            text=(
                "Hi Mak, it's me Amir. I need your help urgently! My bank account "
                "has a problem and I need to pay RM500 right now. Please use this "
                "link to help me: https://urgent-family-pay.example Please don't "
                "call me, I'm in a meeting. Just do it quickly!"
            ),
        ),
    ),
)
