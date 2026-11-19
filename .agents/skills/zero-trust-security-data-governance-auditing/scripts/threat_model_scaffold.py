#!./.venv/bin/python
"""Generate a STRIDE threat-model scaffold from a JSON system description.

Usage: python threat_model_scaffold.py system.json --output THREAT_MODEL.md
Input keys: name, description, components[], data_flows[], trust_boundaries[].
"""

import argparse
import json
import sys
from pathlib import Path

STRIDE = {
    "Spoofing": "strong workload/user identity, MFA, certificate/token validation",
    "Tampering": "integrity protection, signatures, validation, immutable audit logs",
    "Repudiation": "attributed tamper-evident audit events and time synchronization",
    "Information Disclosure": "least privilege, encryption, masking, minimization",
    "Denial of Service": "quotas, rate limits, isolation, autoscaling, graceful degradation",
    "Elevation of Privilege": "deny-by-default authorization, separation of duties, privilege-path tests",
}


def names(values):
    result = []
    for value in values or []:
        result.append(
            str(value.get("name", value.get("id", "unnamed")))
            if isinstance(value, dict)
            else str(value)
        )
    return result


def render(data):
    system = str(data.get("name", "System"))
    components = names(data.get("components"))
    flows = data.get("data_flows", [])
    boundaries = names(data.get("trust_boundaries"))
    lines = [
        f"# STRIDE Threat Model — {system}",
        "",
        f"**System description:** {data.get('description', '[complete description]')}",
        "",
        "## Scope and Assumptions",
        "",
        "- In scope: " + (", ".join(components) or "[components]"),
        "- Trust boundaries: " + (", ".join(boundaries) or "[boundaries]"),
        "- Assets/data classes: [identify value, owner, residency, and retention]",
        "- Adversaries and abuse goals: [identify capabilities and objectives]",
        "",
        "## Data Flows",
        "",
        "| Flow | Source | Destination | Data/classification | Protocol | Boundary crossed |",
        "|---|---|---|---|---|---|",
    ]
    for i, flow in enumerate(flows, 1):
        if isinstance(flow, dict):
            lines.append(
                f"| F-{i:03d} | {flow.get('source', '?')} | {flow.get('destination', flow.get('target', '?'))} | {flow.get('data', '?')} / {flow.get('classification', '?')} | {flow.get('protocol', '?')} | {flow.get('trust_boundary', '?')} |"
            )
        else:
            lines.append(f"| F-{i:03d} | ? | ? | {flow} | ? | ? |")
    if not flows:
        lines.append(
            "| F-001 | [source] | [destination] | [data/class] | [protocol] | [boundary] |"
        )
    lines += [
        "",
        "## STRIDE Analysis",
        "",
        "| Threat ID | Category | Affected component/flow | Threat scenario | Suggested mitigation | Abuse-case test | Residual risk/owner |",
        "|---|---|---|---|---|---|---|",
    ]
    targets = components or ["[component/flow]"]
    n = 1
    for target in targets:
        for category, mitigation in STRIDE.items():
            lines.append(
                f"| THR-{n:03d} | {category} | {target} | [attacker action and impact] | {mitigation} | [test ID and observable result] | [rating/owner/date] |"
            )
            n += 1
    lines += [
        "",
        "## Security Requirements and Verification",
        "",
        "| Control ID | Threats | Requirement | Preventive/detective/recovery | Evidence |",
        "|---|---|---|---|---|",
        "| SEC-001 | THR-001 | [testable control requirement] | [type] | [test/log/config] |",
        "",
        "## Review Triggers",
        "",
        "Reassess when identities, components, interfaces, data classes, vendors, regions, trust boundaries, or deployment topology change.",
    ]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("system", type=Path)
    p.add_argument("--output", "-o", type=Path)
    a = p.parse_args()
    try:
        data = json.loads(a.system.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("input must be a JSON object")
        output = render(data)
        if a.output:
            a.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
