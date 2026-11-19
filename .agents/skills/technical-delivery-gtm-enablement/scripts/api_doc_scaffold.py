#!./.venv/bin/python
"""Scaffold task-oriented Markdown API docs from an OpenAPI JSON/YAML file.

Usage: ./api_doc_scaffold.py openapi.yaml --output-dir docs/api
Creates overview, authentication, quickstart, errors, rate-limits, and tag pages.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an API documentation skeleton from OpenAPI."
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite generated files that already exist",
    )
    return parser.parse_args()


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required for YAML specs (python -m pip install pyyaml)"
        )
    return yaml.safe_load(text)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "untagged"


def write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} exists; use --force to overwrite")
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def operation_stub(method: str, route: str, operation: dict) -> str:
    summary = (
        operation.get("summary")
        or operation.get("operationId")
        or f"{method.upper()} {route}"
    )
    security = operation.get("security")
    responses = operation.get("responses", {})
    response_lines = (
        "\n".join(
            f"- `{code}` — {item.get('description', 'Document response.')}"
            for code, item in responses.items()
        )
        or "- Document success and error responses."
    )
    return f"""## {summary}

`{method.upper()} {route}`  
Operation ID: `{operation.get("operationId", "TODO")}`

{operation.get("description", "Describe the user outcome, permissions, and side effects.")}

**Authentication:** {"Required" if security is not None else "Inherit API default"}

### Request

Document path, query, header, and body fields with constraints and examples.

### Responses

{response_lines}

### Example

```bash
curl --request {method.upper()} "$API_BASE{route}" \\
  --header "Authorization: Bearer $API_TOKEN"
```

"""


def scaffold(spec: dict, output: Path, force: bool) -> int:
    if not str(spec.get("openapi", "")).startswith("3."):
        raise ValueError("spec must declare OpenAPI 3.x")
    info = spec.get("info", {})
    title, version = info.get("title", "API"), info.get("version", "unversioned")
    output.mkdir(parents=True, exist_ok=True)
    tags = defaultdict(list)
    errors = set()
    for route, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_tags = operation.get("tags") or ["Untagged"]
            for tag in operation_tags:
                tags[tag].append((method, route, operation))
            errors.update(
                code
                for code in operation.get("responses", {})
                if str(code).startswith(("4", "5"))
            )

    server = (spec.get("servers") or [{"url": "https://api.example.com"}])[0].get("url")
    files = {
        "overview.md": f"# {title}\n\nVersion: `{version}`\n\n{info.get('description', 'Describe the API purpose and core concepts.')}\n\nBase URL: `{server}`\n",
        "authentication.md": "# Authentication\n\nDocument credential creation, scopes, secure storage, rotation, revocation, and common authentication errors.\n",
        "quickstart.md": f"# Quickstart\n\n1. Obtain a sandbox credential.\n2. Set `API_BASE={server}` and `API_TOKEN`.\n3. Call one primary workflow.\n4. Verify and clean up the result.\n",
        "errors.md": "# Error Catalog\n\nDocument the stable error envelope, correlation ID, retryability, and support path.\n\nObserved status codes: "
        + (", ".join(f"`{code}`" for code in sorted(errors)) or "None declared")
        + "\n",
        "rate-limits.md": "# Rate Limits\n\nDocument limit scope, window, response headers, `429` behavior, retry guidance, quotas, and increase requests.\n",
    }
    for name, content in files.items():
        write(output / name, content, force)
    reference = output / "reference"
    reference.mkdir(exist_ok=True)
    for tag, operations in sorted(tags.items()):
        content = (
            f"# {tag}\n\nEndpoint reference grouped by OpenAPI tag.\n\n"
            + "".join(operation_stub(*item) for item in operations)
        )
        write(reference / f"{slug(tag)}.md", content, force)
    return len(files) + len(tags)


def main() -> int:
    args = parse_args()
    try:
        count = scaffold(load(args.spec), args.output_dir, args.force)
        print(f"generated {count} documentation files in {args.output_dir}")
    except (
        OSError,
        RuntimeError,
        ValueError,
        json.JSONDecodeError,
        yaml.YAMLError if yaml else ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
