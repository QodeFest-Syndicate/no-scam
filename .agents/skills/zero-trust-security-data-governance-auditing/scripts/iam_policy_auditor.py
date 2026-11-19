#!./.venv/bin/python
"""Audit AWS-style IAM policy JSON for common least-privilege violations.

Usage: python iam_policy_auditor.py policy.json [--format text|json]
Exit code 1 indicates findings; this heuristic does not replace IAM simulation.
"""

import argparse
import json
import sys
from pathlib import Path

SENSITIVE = {
    "iam:passrole",
    "iam:createpolicyversion",
    "kms:decrypt",
    "kms:schedulekeydeletion",
    "secretsmanager:getsecretvalue",
    "s3:deletebucket",
    "organizations:*",
}
BROAD = {"s3:*", "iam:*", "kms:*", "ec2:*", "lambda:*", "secretsmanager:*"}


def items(value):
    return value if isinstance(value, list) else [value]


def audit(policy):
    statements = policy.get("Statement", []) if isinstance(policy, dict) else []
    statements = statements if isinstance(statements, list) else [statements]
    findings = []
    has_deny = any(
        isinstance(s, dict) and str(s.get("Effect", "")).lower() == "deny"
        for s in statements
    )
    for i, statement in enumerate(statements, 1):
        if not isinstance(statement, dict):
            findings.append(
                {
                    "severity": "high",
                    "statement": i,
                    "message": "Statement must be an object",
                }
            )
            continue
        effect = str(statement.get("Effect", "Allow"))
        actions = [str(x).lower() for x in items(statement.get("Action", []))]
        resources = [str(x) for x in items(statement.get("Resource", []))]
        if effect.lower() != "allow":
            continue
        if "*" in actions:
            findings.append(
                {
                    "severity": "critical",
                    "statement": i,
                    "message": "Wildcard Action grants all services",
                }
            )
        for action in actions:
            if action in BROAD:
                findings.append(
                    {
                        "severity": "high",
                        "statement": i,
                        "message": f"Overly broad service action: {action}",
                    }
                )
            elif "*" in action:
                findings.append(
                    {
                        "severity": "medium",
                        "statement": i,
                        "message": f"Wildcard action pattern: {action}",
                    }
                )
        if "*" in resources:
            findings.append(
                {
                    "severity": "high",
                    "statement": i,
                    "message": "Wildcard Resource is not least privilege",
                }
            )
        if not statement.get("Condition"):
            findings.append(
                {
                    "severity": "medium",
                    "statement": i,
                    "message": "Allow statement has no contextual Condition",
                }
            )
        if any(a in SENSITIVE for a in actions) and (
            "*" in resources or not statement.get("Condition")
        ):
            findings.append(
                {
                    "severity": "critical",
                    "statement": i,
                    "message": "Sensitive action lacks resource and condition constraints",
                }
            )
    if statements and not has_deny:
        findings.append(
            {
                "severity": "low",
                "statement": None,
                "message": "No explicit Deny guardrail for sensitive operations",
            }
        )
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(findings, key=lambda f: rank[f["severity"]])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy", type=Path)
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    try:
        policy = json.loads(a.policy.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = audit(policy)
    if a.format == "json":
        print(json.dumps({"file": str(a.policy), "findings": findings}, indent=2))
    elif findings:
        for f in findings:
            print(
                f"[{f['severity'].upper()}] statement {f['statement'] or '-'}: {f['message']}"
            )
    else:
        print("PASS: no heuristic least-privilege findings.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
