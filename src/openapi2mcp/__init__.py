"""openapi2mcp: generate an MCP server from an OpenAPI spec.

Public symbols are exposed lazily so the package remains importable while
the implementation is built up module by module.
"""

from openapi2mcp.parser import Param, ToolDef, load_spec

__all__ = ["generate", "load_spec", "extract_tools", "ToolDef", "Param"]


def __getattr__(name):
    if name == "extract_tools":
        from openapi2mcp.parser import extract_tools

        return extract_tools
    if name == "generate":
        from openapi2mcp.generator import generate

        return generate
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
