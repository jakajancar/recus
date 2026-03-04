"""OpenAPI 3.1 schema validation helpers.

Validates JSON values against OpenAPI schemas, resolving $ref pointers
and handling anyOf/oneOf. Extra fields are allowed — only type mismatches
are reported.
"""

from __future__ import annotations

from typing import Any


_JSON_TYPES = {
    type(None): "null",
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
    list: "array",
    dict: "object",
}


def find_response_schema(spec: dict, path_template: str) -> dict | None:
    """Extract the 200/201 JSON response schema for a GET endpoint.

    Args:
        spec: The full parsed OpenAPI spec dict.
        path_template: Path with placeholders, e.g. "/v1/organizations/{slugOrId}".

    Returns:
        The response schema dict, or None if the endpoint has no JSON response defined.
    """
    op = spec.get("paths", {}).get(path_template, {}).get("get", {})
    for code in ("200", "201"):
        resp = op.get("responses", {}).get(code, {})
        json_content = resp.get("content", {}).get("application/json", {})
        if "schema" in json_content:
            return json_content["schema"]
    return None


def find_type_mismatches(spec: dict, schema: dict, value: Any, path: str = "") -> list[str]:
    """Recursively compare a JSON value against an OpenAPI schema.

    Only checks types — extra fields not in the schema are ignored.
    For arrays, only the first 3 items are checked.

    Args:
        spec: The full parsed OpenAPI spec dict (needed to resolve $ref pointers).
        schema: The schema to validate against (may contain $ref, anyOf, oneOf).
        value: The parsed JSON value from the API response.
        path: Dot-separated path for error messages, e.g. "data[0].location.id".

    Returns:
        List of human-readable mismatch descriptions, empty if all types match.
    """
    schema = _resolve(spec, schema)

    for key in ("anyOf", "oneOf"):
        if key in schema:
            best: list[str] | None = None
            for variant in schema[key]:
                sub = find_type_mismatches(spec, variant, value, path)
                if best is None or len(sub) < len(best):
                    best = sub
            return best or []

    jt = _json_type(value)
    if not _type_matches(spec, schema, jt):
        return [f"{path}: got {jt}, expected {schema.get('type')}"]

    issues: list[str] = []
    if jt == "object":
        props = schema.get("properties", {})
        add_props = schema.get("additionalProperties")
        for k, v in value.items():
            child_path = f"{path}.{k}" if path else k
            if k in props:
                issues.extend(find_type_mismatches(spec, props[k], v, child_path))
            elif isinstance(add_props, dict):
                issues.extend(find_type_mismatches(spec, add_props, v, child_path))
    elif jt == "array":
        items_schema = schema.get("items", {})
        for i, item in enumerate(value[:3]):
            issues.extend(find_type_mismatches(spec, items_schema, item, f"{path}[{i}]"))

    return issues


def _resolve(spec: dict, schema: dict) -> dict:
    """Follow $ref chains to the concrete schema."""
    while "$ref" in schema:
        parts = schema["$ref"].lstrip("#/").split("/")
        node = spec
        for p in parts:
            node = node[p]
        schema = node
    return schema


def _type_matches(spec: dict, schema: dict, json_type: str) -> bool:
    schema = _resolve(spec, schema)
    for key in ("anyOf", "oneOf"):
        if key in schema:
            return any(_type_matches(spec, v, json_type) for v in schema[key])
    st = schema.get("type")
    if st is None:
        return True
    if isinstance(st, list):
        return json_type in st or (json_type == "integer" and "number" in st)
    return st == json_type or (json_type == "integer" and st == "number")


def _json_type(value: Any) -> str:
    return _JSON_TYPES.get(type(value), type(value).__name__)
