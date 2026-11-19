#!./.venv/bin/python
"""Generate a Markdown audit checklist for PDPA, GDPR, SOC 2, or HIPAA.

Usage: python compliance_checklist_generator.py --framework gdpr --output checklist.md
This operational aid is not legal advice or certification.
"""

import argparse
import sys
from pathlib import Path

COMMON = {
    "Governance": [
        (
            "Scope systems, data, processors, owners, and audit period",
            "inventory; ownership; scope approval",
        ),
        (
            "Record risks, exceptions, remediation owners, and due dates",
            "risk register; exception approvals",
        ),
    ],
    "Access and security": [
        (
            "Enforce least privilege, MFA, access review, and timely revocation",
            "IAM export; review evidence; termination samples",
        ),
        (
            "Encrypt sensitive data and manage key lifecycle",
            "configuration; key logs; rotation test",
        ),
        (
            "Test incident detection, response, recovery, and notification",
            "exercise report; incident samples",
        ),
    ],
    "Data lifecycle": [
        (
            "Document collection purpose, minimization, retention, and deletion",
            "data map; retention policy; deletion test",
        ),
        (
            "Govern vendors and transfers",
            "contracts; due diligence; transfer assessment",
        ),
    ],
}
SPECIFIC = {
    "pdpa": {
        "Privacy obligations": [
            (
                "Verify notice, consent or other authorized purpose under applicable PDPA",
                "notices; consent records; legal review",
            ),
            (
                "Test access/correction and breach-notification workflows",
                "request samples; breach exercise",
            ),
        ]
    },
    "gdpr": {
        "GDPR obligations": [
            (
                "Document lawful basis, transparency, and records of processing",
                "ROPA; notices; lawful-basis assessment",
            ),
            (
                "Test data-subject rights and one-month response controls",
                "DSAR samples; identity verification",
            ),
            (
                "Assess DPIA, DPO, processor, and cross-border transfer requirements",
                "DPIA; SCC/TIA; DPO record",
            ),
        ]
    },
    "soc2": {
        "Trust Services Criteria": [
            (
                "Map control design and operating effectiveness to scoped criteria",
                "control matrix; population and samples",
            ),
            (
                "Verify change, vulnerability, availability, confidentiality, and monitoring controls",
                "tickets; scans; SLO and alert evidence",
            ),
        ]
    },
    "hipaa": {
        "HIPAA safeguards": [
            (
                "Identify PHI/ePHI and verify minimum-necessary use",
                "data inventory; role matrix",
            ),
            (
                "Verify administrative, physical, and technical safeguards",
                "risk analysis; facility and technical evidence",
            ),
            (
                "Validate BAAs, audit controls, integrity, transmission security, and breach process",
                "BAAs; audit logs; encryption; exercise",
            ),
        ]
    },
}


def render(framework):
    lines = [
        f"# {framework.upper()} Compliance Audit Checklist",
        "",
        "> Status: `[ ]` not tested, `[x]` pass, `[!]` fail, `[-]` not applicable. Record rationale and evidence IDs. This is not legal advice.",
        "",
        "| Control | Status | Specific check | Evidence required | Owner | Notes/remediation |",
        "|---|---|---|---|---|---|",
    ]
    groups = dict(COMMON)
    groups.update(SPECIFIC[framework])
    n = 1
    for category, checks in groups.items():
        for check, evidence in checks:
            lines.append(
                f"| {framework.upper()}-{n:03d} / {category} | [ ] | {check} | {evidence} |  |  |"
            )
            n += 1
    lines += [
        "",
        "## Audit Summary",
        "",
        "- Scope and period:",
        "- Sampling method:",
        "- Pass / fail / N/A totals:",
        "- Material exceptions and residual risk:",
        "- Approver and date:",
    ]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--framework", required=True, choices=sorted(SPECIFIC))
    p.add_argument("--output", "-o", type=Path)
    a = p.parse_args()
    output = render(a.framework)
    try:
        if a.output:
            a.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
