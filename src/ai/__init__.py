"""WatchDog AI - a swarming, evidence-first trust assessment loop (LangGraph + Qwen).

Public surface for the ``service`` layer::

    from ai import assess
    result = assess(request)           # Assessment model
    payload = assess_json(request)     # JSON-safe dict

Importing this package pulls in LangGraph, so a cold process pays ~1s. Long-lived
``service`` processes should import once and reuse the cached graph.
"""

from .api import VERSION, assess, assess_json, health, stream_events
from .schemas import (
    Assessment,
    AssessmentRequest,
    CheckResult,
    CheckStatus,
    Choice,
    CompanionHint,
    RiskLevel,
)

__version__ = VERSION

__all__ = [
    "Assessment",
    "AssessmentRequest",
    "CheckResult",
    "CheckStatus",
    "Choice",
    "CompanionHint",
    "RiskLevel",
    "assess",
    "assess_json",
    "health",
    "stream_events",
    "__version__",
]
