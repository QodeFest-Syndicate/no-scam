#!./.venv/bin/python
"""Generate a lightweight tenant-aware TypeScript SDK from OpenAPI 3.

Usage: sdk_generator.py openapi.json --output client.ts

Supports JSON and YAML OpenAPI documents, component object schemas, operationId
methods, path parameters, JSON request bodies, and JSON success responses.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HTTP = {"get", "post", "put", "patch", "delete"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument(
        "--output", type=Path, help="TypeScript output; defaults to stdout"
    )
    parser.add_argument("--class-name", default="ApiClient")
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
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
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"cannot load OpenAPI spec: {exc}") from exc
    if not isinstance(data, dict) or not str(data.get("openapi", "")).startswith("3."):
        raise ValueError("input must be an OpenAPI 3.x document")
    return data


def pascal(value: str) -> str:
    return (
        "".join(
            part[:1].upper() + part[1:]
            for part in re.split(r"[^A-Za-z0-9]+", value)
            if part
        )
        or "Anonymous"
    )


def ts_type(schema: Any) -> str:
    if not isinstance(schema, dict):
        return "unknown"
    if "$ref" in schema:
        return pascal(str(schema["$ref"]).split("/")[-1])
    if "oneOf" in schema:
        return " | ".join(ts_type(item) for item in schema["oneOf"])
    if schema.get("type") == "array":
        return f"Array<{ts_type(schema.get('items'))}>"
    return {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "object": "Record<string, unknown>",
    }.get(schema.get("type"), "unknown")


def interfaces(spec: dict[str, Any]) -> list[str]:
    output = []
    schemas = spec.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        return output
    for name, schema in schemas.items():
        if not isinstance(schema, dict) or schema.get("type") != "object":
            output.append(f"export type {pascal(name)} = {ts_type(schema)};")
            continue
        required = set(schema.get("required", []))
        fields = []
        for field, definition in schema.get("properties", {}).items():
            optional = "" if field in required else "?"
            fields.append(f"  {json.dumps(field)}{optional}: {ts_type(definition)};")
        output.append(
            f"export interface {pascal(name)} {{\n" + "\n".join(fields) + "\n}"
        )
    return output


def response_type(operation: dict[str, Any]) -> str:
    responses = operation.get("responses", {})
    for code, response in responses.items():
        if str(code).startswith("2") and isinstance(response, dict):
            schema = (
                response.get("content", {}).get("application/json", {}).get("schema")
            )
            return ts_type(schema)
    return "unknown"


def methods(spec: dict[str, Any]) -> list[str]:
    output = []
    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in HTTP or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not operation_id or not re.fullmatch(
                r"[A-Za-z_$][A-Za-z0-9_$]*", str(operation_id)
            ):
                raise ValueError(
                    f"{method.upper()} {path} has no TypeScript-safe operationId"
                )
            path_names = re.findall(r"\{([^}]+)\}", path)
            arguments = [f"{name}: string" for name in path_names]
            body_schema = (
                operation.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            if body_schema:
                arguments.append(f"body: {ts_type(body_schema)}")
            arguments.append(
                "query: Record<string, string | number | boolean | undefined> = {}"
            )
            url = path
            for name in path_names:
                url = url.replace(
                    "{" + name + "}", "${encodeURIComponent(" + name + ")}"
                )
            body_line = ", body: JSON.stringify(body)" if body_schema else ""
            output.append(f'''  async {operation_id}({", ".join(arguments)}): Promise<{response_type(operation)}> {{
    const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])).toString();
    return this.request<{response_type(operation)}>(`{url}${{qs ? `?${{qs}}` : ""}}`, {{ method: "{method.upper()}"{body_line} }});
  }}''')
    return output


def generate(spec: dict[str, Any], class_name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", class_name):
        raise ValueError("--class-name is not a valid TypeScript identifier")
    types = "\n\n".join(interfaces(spec))
    operations = "\n\n".join(methods(spec))
    return f"""/** Generated lightweight SDK. Regenerate from the authoritative OpenAPI contract. */
{types}

export interface ClientOptions {{
  baseUrl: string;
  tenantId: string;
  getAccessToken: () => string | Promise<string>;
  fetchImpl?: typeof fetch;
}}

export class ApiError extends Error {{
  constructor(public status: number, public code: string, message: string, public correlationId?: string, public retryable = false) {{ super(message); }}
}}

export class {class_name} {{
  private readonly fetchImpl: typeof fetch;
  constructor(private readonly options: ClientOptions) {{ this.fetchImpl = options.fetchImpl ?? fetch; }}

  private async request<T>(path: string, init: RequestInit): Promise<T> {{
    const token = await this.options.getAccessToken();
    const response = await this.fetchImpl(`${{this.options.baseUrl.replace(/\\/$/, "")}}${{path}}`, {{
      ...init,
      headers: {{ "Accept": "application/json", "Content-Type": "application/json", "Authorization": `Bearer ${{token}}`, "X-Tenant-ID": this.options.tenantId, ...init.headers }},
    }});
    const payload = response.status === 204 ? undefined : await response.json().catch(() => ({{}}));
    if (!response.ok) {{
      const error = payload as Record<string, unknown>;
      throw new ApiError(response.status, String(error.code ?? "HTTP_ERROR"), String(error.message ?? response.statusText), String(error.correlationId ?? ""), Boolean(error.retryable));
    }}
    return payload as T;
  }}

{operations}
}}
"""


def main() -> int:
    args = parse_args()
    try:
        text = generate(load(args.spec), args.class_name)
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
