#!./.venv/bin/python
"""Generate an onboarding guide and automation manifest from product YAML.

Usage: ./onboarding_flow_generator.py product.yaml --output-dir onboarding
Config supports product, required_integrations, setup_steps, and verification_checks.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a tenant checklist and dependency-aware automation manifest."
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def normalize_steps(config: dict) -> list:
    steps = []
    for integration in config.get("required_integrations", []):
        item = integration if isinstance(integration, dict) else {"name": integration}
        steps.append(
            {
                "id": item.get("id") or f"integrate-{identifier(str(item['name']))}",
                "title": f"Configure {item['name']}",
                "description": item.get(
                    "description", "Authorize and validate the required integration."
                ),
                "depends_on": item.get("depends_on", []),
                "automation": item.get("automation", {}),
            }
        )
    for index, item in enumerate(config.get("setup_steps", []), 1):
        if isinstance(item, str):
            item = {"title": item}
        title = item.get("title") or item.get("name")
        if not title:
            raise ValueError(f"setup step {index} requires a title")
        steps.append(
            {
                "id": item.get("id") or identifier(title),
                "title": title,
                "description": item.get("description", "Complete this setup step."),
                "depends_on": item.get("depends_on", []),
                "automation": item.get("automation", {}),
            }
        )
    ids = [step["id"] for step in steps]
    if len(ids) != len(set(ids)):
        raise ValueError("step IDs must be unique")
    known = set(ids)
    for step in steps:
        unknown = set(step["depends_on"]) - known
        if unknown:
            raise ValueError(
                f"step {step['id']} has unknown dependencies: {sorted(unknown)}"
            )
    return steps


def generate(config: dict) -> tuple:
    steps = normalize_steps(config)
    checks = config.get("verification_checks", [])
    product = config.get("product", config.get("name", "Product"))
    guide = [
        f"# {product} Tenant Onboarding",
        "",
        "## Before you begin",
        "",
        "Confirm tenant owner, region, plan, identity, billing, and data-handling choices.",
        "",
        "## Setup checklist",
        "",
    ]
    for number, step in enumerate(steps, 1):
        dependency = (
            f" Depends on: {', '.join(step['depends_on'])}."
            if step["depends_on"]
            else ""
        )
        guide.extend(
            [
                f"### {number}. {step['title']}",
                "",
                f"- [ ] {step['description']}{dependency}",
                "",
            ]
        )
    guide.extend(["## Verification", ""])
    normalized_checks = []
    for index, check in enumerate(checks, 1):
        item = check if isinstance(check, dict) else {"name": str(check)}
        name = item.get("name") or item.get("title")
        normalized_checks.append(
            {
                "id": item.get("id") or f"verify-{identifier(name)}",
                "name": name,
                "type": item.get("type", "manual"),
                "config": item.get("config", {}),
            }
        )
        guide.append(f"- [ ] {name}")
    guide.extend(
        [
            "",
            "## Completion",
            "",
            "Record activation time, first successful outcome, owner, and support path.",
        ]
    )
    manifest = {
        "schema_version": "1.0",
        "product": product,
        "workflow": {"idempotency_required": True, "resumable": True, "steps": steps},
        "verification_checks": normalized_checks,
        "failure_policy": {
            "retry": "bounded_exponential_backoff",
            "partial_state": "quarantine_and_escalate",
            "credentials": "never_email_or_log",
        },
    }
    return "\n".join(guide) + "\n", manifest


def main() -> int:
    args = parse_args()
    if yaml is None:
        print(
            "error: PyYAML is required (python -m pip install pyyaml)", file=sys.stderr
        )
        return 2
    try:
        config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
        guide, manifest = generate(config)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        outputs = {
            args.output_dir / "onboarding-guide.md": guide,
            args.output_dir / "automation-manifest.json": json.dumps(
                manifest, indent=2, sort_keys=True
            )
            + "\n",
        }
        existing = [str(path) for path in outputs if path.exists() and not args.force]
        if existing:
            raise FileExistsError(f"outputs exist; use --force: {', '.join(existing)}")
        for path, content in outputs.items():
            path.write_text(content, encoding="utf-8")
        print(f"generated onboarding guide and manifest in {args.output_dir}")
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
