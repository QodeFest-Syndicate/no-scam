#!./.venv/bin/python
"""Scaffold an OpenAPI 3.0 BFF contract from YAML/JSON endpoint input.

Usage: bff_contract_scaffold.py spec.yaml [--output openapi.json] [--title NAME]

Input shape: `endpoints` list containing path, method, operationId, summary,
and optional request/response schema mappings. Output is OpenAPI JSON.
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
    parser.add_argument("spec", type=Path)
    parser.add_argument(
        "--output", type=Path, help="OpenAPI JSON path; defaults to stdout"
    )
    parser.add_argument("--title", help="Override API title")
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            value = json.loads(text)
        else:
            try:
                import yaml  # type: ignore
            except ImportError as exc:
                raise ValueError(
                    "YAML input requires PyYAML; provide JSON or install PyYAML"
                ) from exc
            value = yaml.safe_load(text)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"cannot load spec: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("input must be a mapping")
    return value


def schema(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"type": "object", "additionalProperties": True}
    if any(key in value for key in ("type", "$ref", "oneOf", "allOf")):
        return value
    return {
        "type": "object",
        "properties": {
            key: item if isinstance(item, dict) else {"type": str(item)}
            for key, item in value.items()
        },
    }


def generate(source: dict[str, Any], title_override: str | None) -> dict[str, Any]:
    endpoints = source.get("endpoints")
    if not isinstance(endpoints, list) or not endpoints:
        raise ValueError("endpoints must be a non-empty list")
    paths: dict[str, Any] = {}
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            raise ValueError("each endpoint must be a mapping")
        path = endpoint.get("path")
        method = str(endpoint.get("method", "get")).lower()
        operation_id = endpoint.get("operationId") or endpoint.get("operation_id")
        if (
            not isinstance(path, str)
            or not path.startswith("/")
            or method not in {"get", "post", "put", "patch", "delete"}
        ):
            raise ValueError("endpoint requires a valid path and HTTP method")
        if not operation_id or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_]*", str(operation_id)
        ):
            raise ValueError(f"endpoint {path} requires a valid operationId")
        parameters = [
            {"$ref": "#/components/parameters/TenantId"},
            {"$ref": "#/components/parameters/CorrelationId"},
        ]
        if method == "get":
            parameters.extend(
                [
                    {"$ref": "#/components/parameters/Cursor"},
                    {"$ref": "#/components/parameters/PageSize"},
                ]
            )
        operation: dict[str, Any] = {
            "operationId": operation_id,
            "summary": endpoint.get("summary", operation_id),
            "security": [{"bearerAuth": []}],
            "parameters": parameters,
            "responses": {
                str(endpoint.get("status", 200)): {
                    "description": "Success",
                    "content": {
                        "application/json": {"schema": schema(endpoint.get("response"))}
                    },
                },
                "400": {"$ref": "#/components/responses/Error"},
                "401": {"$ref": "#/components/responses/Error"},
                "403": {"$ref": "#/components/responses/Error"},
                "500": {"$ref": "#/components/responses/Error"},
            },
            "x-tenant-scoped": True,
        }
        if method in {"post", "put", "patch"}:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {"schema": schema(endpoint.get("request"))}
                },
            }
            operation["parameters"].append(
                {"$ref": "#/components/parameters/IdempotencyKey"}
            )
        paths.setdefault(path, {})[method] = operation
    return {
        "openapi": "3.0.3",
        "info": {
            "title": title_override or source.get("title", "Tenant BFF API"),
            "version": str(source.get("version", "1.0.0")),
        },
        "servers": source.get("servers", [{"url": "https://api.example.invalid"}]),
        "paths": paths,
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            },
            "parameters": {
                "TenantId": {
                    "name": "X-Tenant-ID",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string"},
                },
                "CorrelationId": {
                    "name": "X-Correlation-ID",
                    "in": "header",
                    "required": False,
                    "schema": {"type": "string"},
                },
                "IdempotencyKey": {
                    "name": "Idempotency-Key",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string"},
                },
                "Cursor": {
                    "name": "cursor",
                    "in": "query",
                    "schema": {"type": "string"},
                },
                "PageSize": {
                    "name": "pageSize",
                    "in": "query",
                    "schema": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 200,
                        "default": 50,
                    },
                },
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "required": ["code", "message", "correlationId"],
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "correlationId": {"type": "string"},
                        "retryable": {"type": "boolean"},
                    },
                }
            },
            "responses": {
                "Error": {
                    "description": "Structured error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    },
                }
            },
        },
    }


def main() -> int:
    args = parse_args()
    try:
        result = generate(load(args.spec), args.title)
        text = json.dumps(result, indent=2, sort_keys=False) + "\n"
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
