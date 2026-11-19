#!./.venv/bin/python
"""Generate normalized JSON RBAC policies from a YAML/JSON role matrix.

Usage: rbac_policy_generator.py --roles-file roles.yaml [--output policy.json]

Input roles may be a mapping keyed by role name or a list with `name` fields.
Permissions may be `resource:action[:scope]` strings or structured mappings.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--roles-file", required=True, type=Path)
    parser.add_argument(
        "--output", type=Path, help="Output JSON path; defaults to stdout"
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            try:
                import yaml  # type: ignore
            except ImportError as exc:
                raise ValueError(
                    "YAML input requires PyYAML; provide JSON or install PyYAML"
                ) from exc
            data = yaml.safe_load(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid role file: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("role file must be a mapping")
    return data


def normalize_permission(value: Any, role: str) -> dict[str, Any]:
    if isinstance(value, str):
        parts = value.split(":")
        if len(parts) not in {2, 3}:
            raise ValueError(
                f"role {role}: permission '{value}' must be resource:action[:scope]"
            )
        resource, action = parts[:2]
        scope = parts[2] if len(parts) == 3 else "tenant"
        result = {"resource": resource, "action": action, "scope": scope}
    elif isinstance(value, dict):
        result = {
            "resource": value.get("resource"),
            "action": value.get("action"),
            "scope": value.get("scope", "tenant"),
        }
        if value.get("conditions"):
            result["conditions"] = value["conditions"]
    else:
        raise ValueError(f"role {role}: permissions must be strings or mappings")
    for field in ("resource", "action", "scope"):
        if not isinstance(result.get(field), str) or not re.fullmatch(
            r"[A-Za-z0-9_.*-]+", result[field]
        ):
            raise ValueError(f"role {role}: invalid permission {field}")
    if result["scope"] not in {"own", "tenant", "workspace", "global"}:
        raise ValueError(f"role {role}: unsupported scope {result['scope']}")
    return result


def generate(spec: dict[str, Any]) -> dict[str, Any]:
    raw_roles = spec.get("roles")
    if isinstance(raw_roles, dict):
        roles = [
            {"name": name, **(body or {})}
            for name, body in raw_roles.items()
            if isinstance(body, dict)
        ]
    elif isinstance(raw_roles, list):
        roles = raw_roles
    else:
        raise ValueError("roles must be a mapping or list")
    output = []
    names = set()
    for role in roles:
        if not isinstance(role, dict) or not isinstance(role.get("name"), str):
            raise ValueError("every role requires a string name")
        name = role["name"]
        if name in names:
            raise ValueError(f"duplicate role: {name}")
        names.add(name)
        permissions = role.get("permissions", [])
        if not isinstance(permissions, list):
            raise ValueError(f"role {name}: permissions must be a list")
        output.append(
            {
                "id": name,
                "description": role.get("description", ""),
                "inherits": role.get("inherits", []),
                "permissions": [
                    normalize_permission(item, name) for item in permissions
                ],
            }
        )
    for role in output:
        unknown = set(role["inherits"]) - names
        if unknown:
            raise ValueError(
                f"role {role['id']}: unknown inherited roles {sorted(unknown)}"
            )
    return {
        "version": str(spec.get("version", "1")),
        "defaultEffect": "deny",
        "tenantContextRequired": True,
        "roles": output,
    }


def main() -> int:
    args = parse_args()
    try:
        policy = generate(load(args.roles_file))
        text = (
            json.dumps(
                policy, indent=2 if args.pretty or args.output else None, sort_keys=True
            )
            + "\n"
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(args.output)
        else:
            sys.stdout.write(text)
        return 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
