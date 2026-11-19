#!./.venv/bin/python
"""Audit Kubernetes YAML and Terraform for common tenant-isolation gaps.

Usage: isolation_audit.py manifests/ [--format text|json] [--strict]

Checks default-deny NetworkPolicy coverage, shared/default service accounts,
cross-namespace references, and wildcard or cluster-admin RBAC. This is a
heuristic preflight and does not replace rendered-manifest policy evaluation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("directory", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 for high/critical findings"
    )
    return parser.parse_args()


def add(
    findings: list[dict[str, Any]],
    severity: str,
    rule: str,
    path: Path,
    message: str,
    line: int = 1,
) -> None:
    findings.append(
        {
            "severity": severity,
            "rule": rule,
            "file": str(path),
            "line": line,
            "message": message,
        }
    )


def line_of(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def audit(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        raise ValueError(f"not a directory: {directory}")
    paths = sorted(
        path
        for path in directory.rglob("*")
        if path.suffix.lower() in {".yaml", ".yml", ".tf"}
    )
    if not paths:
        raise ValueError("no .yaml, .yml, or .tf files found")
    findings: list[dict[str, Any]] = []
    namespaces: dict[str, Path] = {}
    protected: set[str] = set()
    service_accounts: dict[str, set[str]] = defaultdict(set)

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            add(findings, "high", "unreadable-file", path, str(exc))
            continue
        if path.suffix == ".tf":
            for match in re.finditer(
                r"(?i)(?:cluster_role|role)[\s\S]{0,500}(?:resources|verbs)\s*=\s*\[[^\]]*[\"']\*[\"']",
                text,
            ):
                add(
                    findings,
                    "critical",
                    "wildcard-rbac",
                    path,
                    "Terraform RBAC grants wildcard resources or verbs.",
                    line_of(text, match.start()),
                )
            if re.search(r"(?i)cluster-admin", text):
                add(
                    findings,
                    "critical",
                    "cluster-admin-binding",
                    path,
                    "cluster-admin reference detected.",
                )
            if re.search(
                r"(?i)kubernetes_(?:deployment|service|role_binding)", text
            ) and not re.search(r"(?i)namespace\s*=", text):
                add(
                    findings,
                    "high",
                    "missing-namespace",
                    path,
                    "Namespaced Terraform resource has no explicit namespace.",
                )
            continue

        docs = re.split(r"(?m)^---\s*$", text)
        for doc in docs:
            kind_match = re.search(r"(?m)^kind:\s*([^#\s]+)", doc)
            kind = kind_match.group(1) if kind_match else ""
            ns_match = re.search(r"(?m)^\s{2}namespace:\s*([^#\s]+)", doc)
            namespace = ns_match.group(1) if ns_match else "default"
            if kind == "Namespace":
                name_match = re.search(r"(?m)^\s{2}name:\s*([^#\s]+)", doc)
                if name_match and (
                    "tenant" in doc.lower() or name_match.group(1).startswith("tenant-")
                ):
                    namespaces[name_match.group(1)] = path
            if (
                kind == "NetworkPolicy"
                and re.search(r"podSelector:\s*\{\}", doc)
                and "Ingress" in doc
                and "Egress" in doc
            ):
                protected.add(namespace)
            for match in re.finditer(r"(?m)^\s*serviceAccountName:\s*([^#\s]+)", doc):
                account = match.group(1)
                service_accounts[account].add(namespace)
                if account == "default":
                    add(
                        findings,
                        "high",
                        "default-service-account",
                        path,
                        f"Workload in {namespace} uses default service account.",
                        line_of(text, text.find(match.group(0))),
                    )
            if kind in {"Role", "ClusterRole"} and re.search(
                r"(?m)^\s*-\s*[\"']?\*[\"']?\s*$", doc
            ):
                add(
                    findings,
                    "critical",
                    "wildcard-rbac",
                    path,
                    f"{kind} contains wildcard permissions.",
                )
            if kind in {"RoleBinding", "ClusterRoleBinding"} and re.search(
                r"(?m)^\s*name:\s*cluster-admin\s*$", doc
            ):
                add(
                    findings,
                    "critical",
                    "cluster-admin-binding",
                    path,
                    "Binding references cluster-admin.",
                )
            explicit_namespaces = set(
                re.findall(r"(?m)^\s+namespace:\s*([^#\s]+)", doc)
            )
            if namespace != "default" and any(
                value != namespace for value in explicit_namespaces
            ):
                add(
                    findings,
                    "high",
                    "cross-namespace-reference",
                    path,
                    f"Document in {namespace} references {sorted(explicit_namespaces - {namespace})}.",
                )

    for namespace, source in namespaces.items():
        if namespace not in protected:
            add(
                findings,
                "high",
                "missing-default-deny",
                source,
                f"Tenant namespace {namespace} lacks a default-deny ingress+egress NetworkPolicy.",
            )
    for account, used_namespaces in service_accounts.items():
        tenant_namespaces = {ns for ns in used_namespaces if ns.startswith("tenant-")}
        if len(tenant_namespaces) > 1:
            add(
                findings,
                "high",
                "shared-service-account",
                paths[0],
                f"Service account {account} is used across {sorted(tenant_namespaces)}.",
            )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (severity_order[f["severity"]], f["file"], f["line"]))
    return {
        "directory": str(directory),
        "files_scanned": len(paths),
        "tenant_namespaces": sorted(namespaces),
        "findings": findings,
        "finding_count": len(findings),
    }


def main() -> int:
    args = parse_args()
    try:
        report = audit(args.directory)
        if args.format == "json":
            json.dump(report, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        else:
            print(
                f"Isolation audit: {report['files_scanned']} files, {report['finding_count']} findings"
            )
            for finding in report["findings"]:
                print(
                    f"{finding['severity'].upper():8} {finding['file']}:{finding['line']} {finding['rule']}: {finding['message']}"
                )
        severe = any(f["severity"] in {"critical", "high"} for f in report["findings"])
        return 1 if args.strict and severe else 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
