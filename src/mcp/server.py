"""MCP stdio server exposing the same domain logic as the HTTP API."""

from __future__ import annotations

from typing import Literal

from mcp.server.mcpserver import MCPServer

from src.service.domain import recovery, rules
from src.service.domain.scenarios import SCENARIOS
from src.service.domain.types import MessageIn

mcp = MCPServer("no-scam-watchdog")


@mcp.tool()
def assess_message(
    sender: str,
    text: str,
    familiar_contact: bool = True,
    channel: str = "whatsapp",
) -> dict:
    """Check one message for demo warning signs and return visible evidence.

    These are reasons to pause, not proof of a scam. The link is never fetched.
    """
    message = MessageIn(
        sender=sender,
        text=text,
        familiar_contact=familiar_contact,
        channel=channel,
    )
    assessment = rules.assess_with_rules(message)
    return {"assessment": assessment.model_dump(by_alias=True, mode="json")}


@mcp.tool()
def get_recovery_guidance(
    incident: Literal["clicked_link", "entered_credentials", "sent_money", "shared_info"],
) -> dict:
    """Return calm, general next steps after someone has already acted."""
    return recovery.get_recovery(incident).model_dump(by_alias=True, mode="json")


@mcp.tool()
def list_scenarios() -> dict:
    """List the scripted demo scenarios."""
    return {
        "scenarios": [
            scenario.model_dump(by_alias=True, mode="json") for scenario in SCENARIOS
        ]
    }


if __name__ == "__main__":
    mcp.run()
