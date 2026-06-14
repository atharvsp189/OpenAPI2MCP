from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


@dataclass
class Param:
    name: str
    location: str
    required: bool
    schema: dict


@dataclass
class ToolDef:
    name: str
    description: str
    method: str
    path: str
    params: list
    body_schema: Any
    body_required: bool
    input_schema: dict = field(default_factory=dict)


def load_spec(source: str) -> dict:
    """Load an OpenAPI/Swagger spec from an http(s) URL or local json/yaml file,
    with local $refs dereferenced inline."""
    if source.startswith(("http://", "https://")):
        resp = httpx.get(source, timeout=30.0)
        resp.raise_for_status()
        text = resp.text
    else:
        text = Path(source).read_text(encoding="utf-8")
    try:
        spec = json.loads(text)
    except json.JSONDecodeError:
        spec = yaml.safe_load(text)
    return resolve_refs(spec, spec)


def resolve_refs(node, root, _seen=None):
    """Recursively replace local '#/...' $refs with their target. Cycles -> {}."""
    if _seen is None:
        _seen = frozenset()
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/"):
            if ref in _seen:
                return {}
            return resolve_refs(_resolve_pointer(root, ref), root, _seen | {ref})
        return {k: resolve_refs(v, root, _seen) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve_refs(v, root, _seen) for v in node]
    return node


def _resolve_pointer(root, ref):
    cur = root
    for part in ref.lstrip("#/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        cur = cur[part]
    return cur


def _sanitize_path(path: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_")
    return cleaned or "root"


def _sanitize_name(name: str) -> str:
    """Coerce a string into a valid MCP tool name: ^[a-zA-Z0-9_-]{1,64}$.
    Characters outside [A-Za-z0-9_-] are collapsed to '_'; result is trimmed
    and truncated to 64 chars. Returns '' if nothing usable remains."""
    if not name:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_-")
    return cleaned[:64]


def _dedup(name: str, used: dict) -> str:
    if name not in used:
        used[name] = 1
        return name
    n = used[name] + 1
    candidate = f"{name}_{n}"
    while candidate in used:
        n += 1
        candidate = f"{name}_{n}"
    used[name] = n
    used[candidate] = 1
    return candidate


def _extract_body(op: dict):
    """Return (body_schema, body_required, skip_reason)."""
    rb = op.get("requestBody")
    if not rb:
        return None, False, None
    content = rb.get("content", {})
    if "application/json" in content:
        return content["application/json"].get("schema", {}), bool(rb.get("required", False)), None
    ctype = next(iter(content), "unknown")
    return None, False, f"non-JSON request body ({ctype})"


def extract_tools(spec: dict):
    """Walk spec['paths'] -> (list[ToolDef], list[(name, skip_reason)])."""
    from openapi2mcp.schema import build_input_schema

    tools, skipped, used = [], [], {}
    for path, item in (spec.get("paths") or {}).items():
        for method, op in item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            method = method.lower()
            op = op or {}
            body_schema, body_required, skip_reason = _extract_body(op)
            raw_name = _sanitize_name(op.get("operationId")) or f"{method}_{_sanitize_path(path)}"
            if skip_reason:
                skipped.append((raw_name, skip_reason))
                continue
            name = _dedup(raw_name, used)
            description = op.get("summary") or op.get("description") or f"{method.upper()} {path}"
            params = []
            for p in op.get("parameters", []):
                loc = p.get("in")
                if loc not in ("path", "query"):
                    continue
                params.append(
                    Param(
                        name=p["name"],
                        location=loc,
                        required=bool(p.get("required", loc == "path")),
                        schema=p.get("schema", {}),
                    )
                )
            tool = ToolDef(
                name=name,
                description=description,
                method=method,
                path=path,
                params=params,
                body_schema=body_schema,
                body_required=body_required,
            )
            tool.input_schema = build_input_schema(tool)
            tools.append(tool)
    return tools, skipped
