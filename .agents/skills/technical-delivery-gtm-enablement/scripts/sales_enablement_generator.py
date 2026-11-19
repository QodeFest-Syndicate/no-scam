#!./.venv/bin/python
"""Generate sales enablement Markdown assets from a YAML product specification.

Usage: ./sales_enablement_generator.py product.yaml --output-dir sales-kit
Creates feature matrix, elevator pitches, FAQ, and competitive positioning.
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate evidence-oriented sales collateral."
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def cell(value) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "—"
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value if value is not None else "—").replace("|", "\\|")


def matrix(spec: dict) -> str:
    tiers = spec.get("tiers", {})
    if isinstance(tiers, list):
        tiers = {item["name"]: item for item in tiers}
    features = spec.get("features", [])
    names = [
        item.get("name") if isinstance(item, dict) else str(item) for item in features
    ]
    for config in tiers.values():
        names.extend((config.get("features") or {}).keys())
    names = list(dict.fromkeys(names))
    header = (
        "| Feature | " + " | ".join(tiers) + " |\n|---|" + "---|" * len(tiers) + "\n"
    )
    rows = []
    for name in names:
        values = [
            cell((tiers[tier].get("features") or {}).get(name, False)) for tier in tiers
        ]
        rows.append("| " + cell(name) + " | " + " | ".join(values) + " |")
    return "# Feature Comparison\n\n" + header + "\n".join(rows) + "\n"


def pitches(spec: dict) -> str:
    product = spec.get("product", spec.get("name", "Product"))
    differentiators = [
        item.get("claim", item.get("name", "")) if isinstance(item, dict) else str(item)
        for item in spec.get("differentiators", [])
    ]
    differentiators = [item for item in differentiators if item]
    lines = ["# Elevator Pitches", ""]
    for persona in spec.get("target_personas", []):
        item = persona if isinstance(persona, dict) else {"name": str(persona)}
        name, problem = (
            item.get("name"),
            item.get("problem", "their highest-priority workflow"),
        )
        outcome = item.get(
            "outcome",
            spec.get(
                "primary_outcome", "reach value faster with less operational risk"
            ),
        )
        proof = item.get("proof", "[insert validated customer or product evidence]")
        lines.extend(
            [
                f"## {name}",
                "",
                f"{product} helps {name} solve {problem} so they can {outcome}. "
                f"Unlike manual or fragmented alternatives, it provides {', '.join(differentiators) or '[validated differentiator]'}. Proof: {proof}.",
                "",
            ]
        )
    return "\n".join(lines)


def faq(spec: dict) -> str:
    items = spec.get("faq", [])
    lines = ["# Sales FAQ", ""]
    defaults = [
        (
            "Who is this for?",
            "Use the approved ideal-customer profile and disqualifiers.",
        ),
        (
            "How is it priced?",
            "Explain tier, usage metric, allowance, overage, and contract assumptions.",
        ),
        (
            "How is customer data protected?",
            "Use current security evidence; do not claim unverified certification.",
        ),
        (
            "How long does implementation take?",
            "Use the standard onboarding path and state customer dependencies.",
        ),
    ]
    if not items:
        items = [{"question": q, "answer": a} for q, a in defaults]
    for item in items:
        lines.extend(
            [
                f"## {item.get('question')}",
                "",
                item.get("answer", "[approved answer required]"),
                "",
            ]
        )
    return "\n".join(lines)


def positioning(spec: dict) -> str:
    lines = [
        "# Competitive Positioning",
        "",
        "Use truthful, evidence-backed comparisons. Escalate unknown claims.",
        "",
        "## Differentiators",
        "",
    ]
    for item in spec.get("differentiators", []):
        detail = item if isinstance(item, dict) else {"claim": str(item)}
        lines.append(
            f"- **{detail.get('claim', detail.get('name'))}:** {detail.get('evidence', '[link current evidence]')}"
        )
    lines.extend(["", "## Alternatives", ""])
    for item in spec.get("alternatives", []):
        detail = item if isinstance(item, dict) else {"name": str(item)}
        lines.extend(
            [
                f"### {detail.get('name')}",
                "",
                f"**Best when:** {detail.get('best_when', '[document fairly]')}",
                f"**Our advantage:** {detail.get('our_advantage', '[evidence required]')}",
                f"**Do not claim:** {detail.get('prohibited_claim', 'Unverified inferiority or unsupported feature gaps.')}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if yaml is None:
        print(
            "error: PyYAML is required (python -m pip install pyyaml)", file=sys.stderr
        )
        return 2
    try:
        spec = yaml.safe_load(args.spec.read_text(encoding="utf-8")) or {}
        outputs = {
            "feature-comparison.md": matrix(spec),
            "elevator-pitches.md": pitches(spec),
            "faq.md": faq(spec),
            "competitive-positioning.md": positioning(spec),
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        existing = [
            name
            for name in outputs
            if (args.output_dir / name).exists() and not args.force
        ]
        if existing:
            raise FileExistsError(f"outputs exist; use --force: {', '.join(existing)}")
        for name, content in outputs.items():
            (args.output_dir / name).write_text(
                content.rstrip() + "\n", encoding="utf-8"
            )
        print(f"generated {len(outputs)} sales assets in {args.output_dir}")
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
