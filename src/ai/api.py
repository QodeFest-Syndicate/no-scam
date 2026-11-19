"""Public API consumed by ``service``.

Two integration shapes, one contract:

* in-process  - ``assess`` / ``assess_json`` / ``stream_events``
* process      - ``python -m ai`` reads one JSON request on stdin, writes one
                 JSON assessment on stdout (see ``cli.py``)
"""

from __future__ import annotations

from typing import Any, Iterator

from .config import resolve_settings
from .graph import RECURSION_LIMIT, build_graph, initial_state
from .schemas import Assessment, AssessmentRequest

VERSION = "0.1.0"
PACKAGE = "ai"


def _coerce(request: AssessmentRequest | dict[str, Any]) -> AssessmentRequest:
    if isinstance(request, AssessmentRequest):
        return request
    return AssessmentRequest.model_validate(request)


def resolve_mode(request: AssessmentRequest) -> str:
    """Turn the caller's preference into a concrete mode (``auto`` or ``offline``)."""
    if request.mode == "offline":
        return "offline"
    return "auto" if resolve_settings(request.mode) is not None else "offline"


def assess(request: AssessmentRequest | dict[str, Any], *, mode: str | None = None) -> Assessment:
    """Run the full swarm once and return the validated assessment."""
    req = _coerce(request)
    if mode is not None:
        req = req.model_copy(update={"mode": mode})
    state = initial_state(req, resolve_mode(req))
    result = build_graph().invoke(state, config={"recursion_limit": RECURSION_LIMIT})
    assessment = result.get("assessment")
    if assessment is None:  # pragma: no cover - defensive contract check
        raise RuntimeError("swarm returned no assessment")
    return assessment


def assess_json(request: AssessmentRequest | dict[str, Any], *, mode: str | None = None) -> dict[str, Any]:
    """Same as :func:`assess`, serialised for HTTP/stdio transport."""
    return assess(request, mode=mode).model_dump(mode="json")


def stream_events(
    request: AssessmentRequest | dict[str, Any],
    *,
    mode: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield one chunk per completed node so ``ui`` can show progress.

    The last chunk carries ``"done": True`` and the full assessment.
    """
    req = _coerce(request)
    if mode is not None:
        req = req.model_copy(update={"mode": mode})
    state = initial_state(req, resolve_mode(req))
    graph = build_graph()

    for update in graph.stream(state, stream_mode="updates", config={"recursion_limit": RECURSION_LIMIT}):
        if not isinstance(update, dict):
            continue
        for node, delta in update.items():
            payload = delta if isinstance(delta, dict) else {}
            assessment = payload.get("assessment")
            yield {
                "node": node,
                "events": payload.get("events", []),
                "done": assessment is not None,
                "assessment": assessment.model_dump(mode="json") if assessment is not None else None,
            }


def health() -> dict[str, Any]:
    """Readiness probe for ``service``. Never exposes credentials."""
    settings = resolve_settings("auto")
    return {
        "package": PACKAGE,
        "version": VERSION,
        "offline_capable": True,
        "llm_enabled": settings is not None,
        "model": settings.model if settings else None,
        "gateway": settings.base_url if settings else None,
    }
