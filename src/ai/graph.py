"""The LangGraph swarm: fan-out specialists, then a bounded critique/judge repair loop.

    START -> intake -> triage --(Send xN)--> specialist(s) -> synthesis
          -> critique -> judge --pass--> finalize -> END
                            \\--fail (attempts <= max_revisions)--> synthesis
"""

from __future__ import annotations

import time
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .nodes.critique import critique_node
from .nodes.finalize import finalize_node
from .nodes.intake import intake_node
from .nodes.judge import judge_node
from .nodes.specialists import specialist_node
from .nodes.synthesis import synthesis_node
from .nodes.triage import dispatch_specialists, triage_node
from .schemas import AssessmentRequest
from .state import WatchdogState

RECURSION_LIMIT = 60


def initial_state(request: AssessmentRequest, llm_mode: str) -> WatchdogState:
    return WatchdogState(
        request=request,
        llm_mode=llm_mode,
        started_at=time.time(),
        findings=[],
        checks=[],
        events=[],
        attempts=0,
    )


def route_after_judge(state: WatchdogState) -> str:
    verdict = state.get("judge")
    if verdict is not None and verdict.passed:
        return "finalize"
    if state.get("attempts", 1) > state["request"].max_revisions:
        return "finalize"
    return "revise"


@lru_cache(maxsize=1)
def build_graph():
    builder = StateGraph(WatchdogState)

    builder.add_node("intake", intake_node)
    builder.add_node("triage", triage_node)
    builder.add_node("specialist", specialist_node)
    builder.add_node("synthesis", synthesis_node)
    builder.add_node("critique", critique_node)
    builder.add_node("judge", judge_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "triage")
    builder.add_conditional_edges("triage", dispatch_specialists, ["specialist"])
    builder.add_edge("specialist", "synthesis")
    builder.add_edge("synthesis", "critique")
    builder.add_edge("critique", "judge")
    builder.add_conditional_edges(
        "judge",
        route_after_judge,
        {"revise": "synthesis", "finalize": "finalize"},
    )
    builder.add_edge("finalize", END)

    return builder.compile()
