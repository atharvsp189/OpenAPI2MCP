from __future__ import annotations

import pprint
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from openapi2mcp.parser import extract_tools, load_spec

TEMPLATE_DIR = Path(__file__).parent / "templates"
_OUTPUT_FILES = {
    "tools.py": "tools.py.j2",
    "executor.py": "executor.py.j2",
    "server.py": "server.py.j2",
    "pyproject.toml": "pyproject.toml.j2",
    "README.md": "README.md.j2",
}


def _default_base_url(spec: dict) -> str:
    servers = spec.get("servers") or []
    if servers and isinstance(servers[0], dict):
        url = servers[0].get("url", "")
        if url.startswith("http") and "{" not in url:
            return url
    return "http://localhost:8000"


def _tool_to_dict(t) -> dict:
    body_keys, body_raw = [], False
    if t.body_schema is not None:
        body = t.body_schema
        if body.get("type") == "object" and "properties" in body:
            body_keys = list(body["properties"].keys())
        else:
            body_raw = True
    return {
        "name": t.name,
        "description": t.description,
        "method": t.method,
        "path": t.path,
        "input_schema": t.input_schema,
        "path_params": [p.name for p in t.params if p.location == "path"],
        "query_params": [p.name for p in t.params if p.location == "query"],
        "body_keys": body_keys,
        "body_raw": body_raw,
        "has_body": t.body_schema is not None,
    }


def generate(spec: str, out_dir: str, server_name: str = "generated-mcp"):
    """Generate a Python MCP server from an OpenAPI spec (URL or file path).
    Returns (tools, skipped)."""
    spec_doc = load_spec(spec)
    tools, skipped = extract_tools(spec_doc)
    tools_literal = pprint.pformat([_tool_to_dict(t) for t in tools], indent=4, sort_dicts=False, width=100)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False, keep_trailing_newline=True)
    ctx = {
        "tools_literal": tools_literal,
        "skipped": skipped,
        "default_base_url": _default_base_url(spec_doc),
        "server_name": server_name,
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for fname, template in _OUTPUT_FILES.items():
        (out / fname).write_text(env.get_template(template).render(**ctx), encoding="utf-8")
    return tools, skipped
