#!./.venv/bin/python
"""Bootstrap a local file-based schema/contract registry manifest.

Usage:
  contract_registry_init.py schemas/ --output registry/index.json \
    --compatibility BACKWARD --owner data-platform [--metadata owners.json]

JSON schema files are grouped by subject and version from document metadata or
filenames such as ``orders-1.2.0.json``. The manifest records hashes and version
history without copying or changing source files.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION_SUFFIX = re.compile(r"^(?P<subject>.+?)[._-]v?(?P<version>\d+(?:\.\d+){0,2})$")


def parse_document(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
            except ImportError as exc:
                raise ValueError("YAML files require PyYAML") from exc
            value = yaml.safe_load(text)
        else:
            value = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be an object")
    return value


def subject_version(path: Path, data: dict[str, Any]) -> tuple[str, str]:
    subject = data.get("subject") or data.get("name") or data.get("title")
    version = data.get("version") or data.get("schemaVersion")
    stem = path.name
    for suffix in (".schema.json", ".proto.json", ".avsc", ".json", ".yaml", ".yml"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    match = VERSION_SUFFIX.match(stem)
    if not subject:
        subject = match.group("subject") if match else stem
    if not version:
        version = match.group("version") if match else "1.0.0"
    pieces = str(version).lstrip("v").split(".")
    version = (
        ".".join(pieces + ["0"] * (3 - len(pieces)))
        if len(pieces) <= 3
        else str(version)
    )
    return str(subject), version


def version_key(version: str) -> tuple[Any, ...]:
    return tuple(int(x) if x.isdigit() else x for x in re.split(r"[.-]", version))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "schema_dir", type=Path, help="directory containing JSON/YAML schema files"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("registry-index.json"), help="manifest path"
    )
    parser.add_argument(
        "--compatibility",
        choices=("BACKWARD", "FORWARD", "FULL", "NONE"),
        default="BACKWARD",
    )
    parser.add_argument("--owner", required=True, help="default owner for subjects")
    parser.add_argument(
        "--metadata",
        type=Path,
        help="optional JSON object mapping subjects to owner metadata",
    )
    parser.add_argument("--recursive", action="store_true", help="scan subdirectories")
    parser.add_argument(
        "--overwrite", action="store_true", help="replace an existing manifest"
    )
    args = parser.parse_args()
    if not args.schema_dir.is_dir():
        parser.error(f"schema directory not found: {args.schema_dir}")
    if args.output.exists() and not args.overwrite:
        parser.error(f"output already exists: {args.output}; use --overwrite")
    metadata: dict[str, Any] = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
            if not isinstance(metadata, dict):
                raise ValueError("metadata root must be an object")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"error: cannot load metadata: {exc}", file=sys.stderr)
            return 2
    globber = args.schema_dir.rglob if args.recursive else args.schema_dir.glob
    files = sorted(
        {
            path
            for pattern in ("*.json", "*.avsc", "*.yaml", "*.yml")
            for path in globber(pattern)
            if path.resolve() != args.output.resolve()
        }
    )
    if not files:
        print("error: no schema files found", file=sys.stderr)
        return 2
    subjects: dict[str, dict[str, Any]] = {}
    try:
        for path in files:
            raw = path.read_bytes()
            data = parse_document(path)
            subject, version = subject_version(path, data)
            entry = subjects.setdefault(
                subject,
                {
                    "owner": metadata.get(subject, args.owner),
                    "compatibility": args.compatibility,
                    "versions": [],
                },
            )
            if any(item["version"] == version for item in entry["versions"]):
                raise ValueError(f"duplicate version {subject} {version}")
            entry["versions"].append(
                {
                    "version": version,
                    "path": str(path.resolve().relative_to(args.schema_dir.resolve())),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "format": "avro" if path.suffix == ".avsc" else "json/yaml",
                }
            )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for entry in subjects.values():
        entry["versions"].sort(key=lambda item: version_key(item["version"]))
        entry["latest"] = entry["versions"][-1]["version"]
    manifest = {
        "registry_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "schema_root": str(args.schema_dir.resolve()),
        "subjects": subjects,
    }
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
        return 2
    print(
        f"Created {args.output} with {len(subjects)} subjects and {len(files)} versions"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
