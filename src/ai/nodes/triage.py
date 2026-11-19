"""Triage: the supervisor picks the smallest useful set of specialists."""

from __future__ import annotations

from langgraph.types import Send

from ..schemas import IncidentProfile
from ..state import SpecialistTask, WatchdogState, trace_event

SPECIALISTS: dict[str, str] = {
    "signal_analyst": "Name only the pressure patterns visible in the supplied text.",
    "perimeter_analyst": "Compare the claimed identity with the saved contacts and their usual routes.",
    "link_inspector": "Report what the reputation lookup returned for each link in the message.",
    "recovery_advisor": "Give calm, ordered next steps for someone who already clicked or paid.",
}


def plan_for(profile: IncidentProfile) -> list[str]:
    """Selective, event-triggered checks: never dispatch a specialist without a reason."""
    plan = ["signal_analyst", "perimeter_analyst"]
    if profile.links:
        plan.append("link_inspector")
    if profile.already_acted:
        plan.append("recovery_advisor")
    return plan


def triage_node(state: WatchdogState) -> dict:
    plan = plan_for(state["profile"])
    skipped = [agent for agent in SPECIALISTS if agent not in plan]
    return {
        "plan": plan,
        "events": [
            trace_event(
                "triage",
                f"Dispatched {len(plan)} specialists in parallel.",
                agents=plan,
                skipped=skipped,
            )
        ],
    }


def dispatch_specialists(state: WatchdogState) -> list[Send]:
    """Fan-out: one Send per planned specialist, all running in the same superstep."""
    return [
        Send(
            "specialist",
            {
                "request": state["request"],
                "profile": state["profile"],
                "llm_mode": state["llm_mode"],
                "task": SpecialistTask(agent=agent, objective=SPECIALISTS[agent]),
            },
        )
        for agent in state.get("plan", [])
    ]
