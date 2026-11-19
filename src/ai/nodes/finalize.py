"""Finalize: stamp timing, rubric score and the full step trace onto the answer."""

from __future__ import annotations

import time

from ..state import WatchdogState, trace_event


def finalize_node(state: WatchdogState) -> dict:
    draft = state["draft"]
    if draft is None:  # defensive: a graph bug must not return a half-empty contract
        raise RuntimeError("swarm finished without an assessment draft")

    judge = state.get("judge")
    events = list(state.get("events", []))
    elapsed_ms = int((time.time() - state.get("started_at", time.time())) * 1000)
    final_event = trace_event(
        "finalize",
        f"Assessment ready: {draft.verdict.value}.",
        verdict=draft.verdict.value,
        rubric_score=judge.score if judge else None,
        elapsed_ms=elapsed_ms,
    )

    assessment = draft.model_copy(
        update={
            "revisions": max(0, state.get("attempts", 1) - 1),
            "rubric_score": round(judge.score, 2) if judge else 0.0,
            "elapsed_ms": elapsed_ms,
            "trace": [*events, final_event],
        }
    )
    return {"assessment": assessment, "events": [final_event]}
