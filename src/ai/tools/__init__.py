"""Deterministic tools the swarm may consult without a model."""

from .perimeter import match_contact, normalize_handle, route_is_known
from .reputation import ReputationResult, extract_links, lookup, summarize
from .signals import analyze_incident, detect_amount

__all__ = [
    "ReputationResult",
    "analyze_incident",
    "detect_amount",
    "extract_links",
    "lookup",
    "match_contact",
    "normalize_handle",
    "route_is_known",
    "summarize",
]
