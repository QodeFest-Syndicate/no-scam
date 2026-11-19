#!./.venv/bin/python
"""Generate Kubernetes tenant baseline manifests.

Usage:
  tenant_provisioner.py --tenant-id acme --tier pro --region us-east-1 \
    --resource-quotas '{"cpu":"8","memory":"16Gi","storage":"100Gi"}'
  tenant_provisioner.py ... --output acme.yaml

Output includes Namespace, ResourceQuota, default-deny NetworkPolicy, and a
tenant administrator RoleBinding. Review identity subjects before applying.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULTS = {
    "free": {"cpu": "2", "memory": "4Gi", "storage": "20Gi", "pods": "20"},
    "pro": {"cpu": "16", "memory": "32Gi", "storage": "500Gi", "pods": "100"},
    "enterprise": {"cpu": "64", "memory": "128Gi", "storage": "2Ti", "pods": "500"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--tier", required=True, choices=DEFAULTS)
    parser.add_argument("--region", required=True)
    parser.add_argument(
        "--resource-quotas", default="{}", help="JSON object overriding tier defaults"
    )
    parser.add_argument(
        "--admin-group", help="RBAC group; defaults to tenant:TENANT_ID:admins"
    )
    parser.add_argument(
        "--output", type=Path, help="Write YAML to this path instead of stdout"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite --output if it exists"
    )
    return parser.parse_args()


def dns_label(value: str, field: str) -> str:
    normalized = value.lower().replace("_", "-")
    if not re.fullmatch(r"[a-z0-9](?:[-a-z0-9]{0,61}[a-z0-9])?", normalized):
        raise ValueError(f"{field} must be a valid Kubernetes DNS label")
    return normalized


def yaml_scalar(value: Any) -> str:
    text = str(value)
    if not re.fullmatch(r"[A-Za-z0-9_.:/+-]+", text):
        return json.dumps(text)
    return text


def build_manifest(
    tenant: str, tier: str, region: str, quotas: dict[str, Any], group: str
) -> str:
    namespace = f"tenant-{tenant}"
    hard = {**DEFAULTS[tier], **quotas}
    known = {
        "cpu": "requests.cpu",
        "memory": "requests.memory",
        "storage": "requests.storage",
        "pods": "pods",
    }
    unknown = sorted(set(hard) - set(known))
    if unknown:
        raise ValueError(f"unsupported quota keys: {', '.join(unknown)}")
    if any(
        str(value).strip().startswith("-") or not str(value).strip()
        for value in hard.values()
    ):
        raise ValueError("quota values must be non-negative and non-empty")
    quota_lines = "\n".join(
        f"    {known[key]}: {yaml_scalar(hard[key])}" for key in known
    )
    return f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
  labels:
    platform.example.com/tenant-id: {tenant}
    platform.example.com/tier: {tier}
    platform.example.com/region: {region}
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: {namespace}
  labels:
    platform.example.com/tenant-id: {tenant}
spec:
  hard:
{quota_lines}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes: [Ingress, Egress]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-admins
  namespace: {namespace}
subjects:
  - kind: Group
    name: {yaml_scalar(group)}
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: tenant-namespace-admin
  apiGroup: rbac.authorization.k8s.io
"""


def main() -> int:
    args = parse_args()
    try:
        tenant = dns_label(args.tenant_id, "--tenant-id")
        region = dns_label(args.region, "--region")
        try:
            quotas = json.loads(args.resource_quotas)
        except json.JSONDecodeError as exc:
            raise ValueError(f"--resource-quotas is not valid JSON: {exc}") from exc
        if not isinstance(quotas, dict):
            raise ValueError("--resource-quotas must be a JSON object")
        group = args.admin_group or f"tenant:{tenant}:admins"
        manifest = build_manifest(tenant, args.tier, region, quotas, group)
        if args.output:
            if args.output.exists() and not args.force:
                raise ValueError(
                    f"output exists: {args.output}; pass --force to overwrite"
                )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(manifest, encoding="utf-8")
            print(args.output)
        else:
            sys.stdout.write(manifest)
        return 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
