#!./.venv/bin/python
"""Check a filled handover file for missing answers and sections."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

TEMPLATES = {
    "s1": "S1-domain-scoping-handover.md",
    "s2": "S2-architecture-handover.md",
    "s3": "S3-task-plan-handover.md",
    "s4": "S4-pre-build-gate-handover.md",
    "s5": "S5-build-completion-handover.md",
    "s6": "S6-deployment-handover.md",
    "s7": "S7-validation-handover.md",
    "s8": "S8-delivery-handover.md",
    "security": "security-audit-handover.md",
    "data": "data-pipeline-handover.md",
    "ai": "ai-ml-handover.md",
    "incident": "incident-postmortem-handover.md",
}

ALIASES = {
    "domain": "s1",
    "domain-scoping": "s1",
    "s1-domain-scoping": "s1",
    "architecture": "s2",
    "s2-architecture": "s2",
    "task-plan": "s3",
    "s3-task-plan": "s3",
    "pre-build-gate": "s4",
    "s4-pre-build-gate": "s4",
    "build-completion": "s5",
    "s5-build-completion": "s5",
    "deployment": "s6",
    "s6-deployment": "s6",
    "validation": "s7",
    "s7-validation": "s7",
    "delivery": "s8",
    "s8-delivery": "s8",
    "security-audit": "security",
    "data-pipeline": "data",
    "ai-ml": "ai",
    "ai/ml": "ai",
    "incident-postmortem": "incident",
}

H2_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_PATTERN = re.compile(r"\[[A-Z✅❌⚠️][A-Z0-9 ✅❌⚠️/_-]*\]")
EXAMPLE_HEADING = "what does a filled example look like?"


def simple_name(value: str) -> str:
    """Make a template name easy to match."""
    name = Path(value).name.lower().strip()
    name = name.removesuffix(".md")
    name = name.removesuffix("-handover")
    return ALIASES.get(name, name)


def template_path(value: str) -> Path:
    """Find the chosen built-in template."""
    key = simple_name(value)
    if key not in TEMPLATES:
        names = ", ".join(TEMPLATES)
        raise ValueError(f"unknown template '{value}'. Use one of: {names}")
    return Path(__file__).resolve().parent.parent / "references" / TEMPLATES[key]


def headings(text: str) -> list[str]:
    """Get all level-two question headings."""
    return [match.group(1).strip() for match in H2_PATTERN.finditer(text)]


def clean_heading(value: str) -> str:
    """Make heading matching ignore case and extra spaces."""
    return " ".join(value.casefold().split())


def required_headings(template_text: str) -> list[str]:
    """Get required headings, but skip the example block."""
    return [
        heading
        for heading in headings(template_text)
        if clean_heading(heading) != EXAMPLE_HEADING
    ]


def empty_headings(text: str, required: list[str]) -> list[str]:
    """Find required sections with no words below them."""
    matches = list(H2_PATTERN.finditer(text))
    required_names = {clean_heading(item): item for item in required}
    empty = []
    for index, match in enumerate(matches):
        name = clean_heading(match.group(1))
        if name not in required_names:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if not body:
            empty.append(required_names[name])
    return empty


def placeholder_gaps(text: str) -> list[tuple[int, str]]:
    """Find blank prompts and their line numbers."""
    gaps = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in PLACEHOLDER_PATTERN.finditer(line):
            gaps.append((line_number, match.group(0)))
    return gaps


def read_text(path: Path, label: str) -> str:
    """Read one text file or stop with a clear error."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read {label} '{path}': {exc}") from exc
    if not text.strip():
        raise ValueError(f"{label} '{path}' is empty")
    return text


def completion_score(
    template_text: str,
    required: list[str],
    missing: list[str],
    empty: list[str],
    gaps: list[tuple[int, str]],
) -> int:
    """Count filled prompts and present, non-empty sections."""
    template_slots = len(PLACEHOLDER_PATTERN.findall(template_text))
    total = len(required) + template_slots
    lost = len(missing) + len(empty) + len(gaps)
    if total == 0:
        return 100
    return max(0, round(100 * (total - min(lost, total)) / total))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a filled handover file for missing answers."
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Template type. Example: S1, security, data, ai, or incident.",
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Filled handover Markdown file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source_path = template_path(args.template)
        template_text = read_text(source_path, "template")
        filled_text = read_text(args.file, "filled file")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    required = required_headings(template_text)
    actual_names = {clean_heading(item) for item in headings(filled_text)}
    missing = [item for item in required if clean_heading(item) not in actual_names]
    empty = empty_headings(filled_text, required)
    gaps = placeholder_gaps(filled_text)
    percent = completion_score(template_text, required, missing, empty, gaps)

    print(f"Complete: {percent}%")
    print(f"File: {args.file}")
    print(f"Template: {source_path.name}")

    if missing:
        print("\nMissing question headings:")
        for item in missing:
            print(f"  ❌ {item}")

    if empty:
        print("\nQuestion headings with no answer:")
        for item in empty:
            print(f"  ❌ {item}")

    if gaps:
        print("\nBlank prompts:")
        counts = Counter(value for _, value in gaps)
        for value, count in sorted(counts.items()):
            lines = [str(line) for line, found in gaps if found == value]
            print(f"  ⚠️ {value}: {count} left. Lines {', '.join(lines)}")

    if not missing and not empty and not gaps:
        print("\n✅ Done. No gaps found.")
        return 0

    print("\n❌ Not done. Fill every gap.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
