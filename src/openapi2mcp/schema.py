from __future__ import annotations

from copy import deepcopy


def _schema_from_param(param) -> dict:
    schema = deepcopy(param.schema or {})
    if not schema:
        schema = {"type": "string"}
    return schema


def build_input_schema(tool) -> dict:
    properties = {}
    required = []

    for param in tool.params:
        properties[param.name] = _schema_from_param(param)
        if param.required:
            required.append(param.name)

    if tool.body_schema is not None:
        if tool.body_required:
            required.append("body")
        if tool.body_schema.get("type") == "object" and "properties" in tool.body_schema:
            properties["body"] = deepcopy(tool.body_schema)
        else:
            properties["body"] = deepcopy(tool.body_schema)

    schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema
