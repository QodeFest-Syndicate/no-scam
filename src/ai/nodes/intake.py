"""Intake: read the incident once, deterministically, before spending any model call."""

from __future__ import annotations

from ..schemas import CheckResult, CheckStatus, TrustedContact
from ..state import WatchdogState, trace_event
from ..tools.perimeter import match_contact
from ..tools.signals import analyze_incident


def _contact_for(state: WatchdogState) -> TrustedContact | None:
    incident = state["request"].incident
    return match_contact(
        handle=incident.sender_handle,
        display_name=incident.sender_display_name,
        perimeter=incident.perimeter,
    )


def baseline_checks(state: WatchdogState) -> list[CheckResult]:
    """Two checks exist before any specialist runs, so the UI can always show them."""
    contact = _contact_for(state)
    checks: list[CheckResult] = []

    if contact and contact.known_handles:
        checks.append(
            CheckResult(
                id="contact_route",
                label=f"Your saved number for {contact.name}",
                kind="contact_route",
                source="your saved contacts",
                status=CheckStatus.not_run,
                result=(
                    f"Not run yet. The independent step is to call {contact.known_handles[0]} "
                    "yourself, outside this conversation."
                ),
                simulated=False,
            )
        )
    else:
        checks.append(
            CheckResult(
                id="contact_route",
                label="Independent contact route",
                kind="contact_route",
                source="your saved contacts",
                status=CheckStatus.unavailable,
                result=(
                    "No saved number is on file for this sender, so there is no separate "
                    "route to check them yet."
                ),
                simulated=False,
            )
        )

    checks.append(
        CheckResult(
            id="official_source",
            label="Official source lookup (PDRM / bank)",
            kind="official_source",
            source="not connected in this build (simulated placeholder)",
            status=CheckStatus.unavailable,
            result=(
                "No live official source is connected. This build does not claim any "
                "official verification or clearance."
            ),
            simulated=True,
        )
    )
    return checks


def intake_node(state: WatchdogState) -> dict:
    request = state["request"]
    profile = analyze_incident(request)
    checks = baseline_checks(state)
    return {
        "profile": profile,
        "checks": checks,
        "attempts": 0,
        "events": [
            trace_event(
                "intake",
                "Incident profiled from the supplied text and saved contacts.",
                channel=profile.channel.value,
                risk_score=profile.risk_score,
                baseline_band=profile.baseline_band.value,
                links=profile.links,
                checks=[check.id for check in checks],
            )
        ],
    }
