"""Validate OpenAPI schema against live API responses.

Dynamically discovers all GET endpoints from docs/openapi.yaml and creates
one test per endpoint. Each test hits the live API and validates that
response types match the schema.

Usage:
    uv run pytest tests/test_api.py -v
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

from recus.client import AnonClient, AuthClient

from .conftest import SeedIds
from .schema import find_response_schema, find_type_mismatches

_SPEC_PATH = Path(__file__).resolve().parent.parent / "docs" / "openapi.yaml"
_SPEC: dict = yaml.safe_load(_SPEC_PATH.read_text())

# Query params not marked required in the spec but needed for meaningful responses.
_EFFECTIVELY_REQUIRED: dict[str, list[str]] = {
    "/v1/locations/availability": ["organizationSlug"],  # returns empty without org filter
    "/v1/instructors/cards/lessons": ["organizationSlug"],  # returns empty without org filter
    "/v1/discovery/programmed": ["organizationId"],  # requires at least one of organizationId/locationId/regionId/instructorId
}


@dataclass
class Endpoint:
    """A GET endpoint parsed from the OpenAPI spec."""

    path: str
    """URL template, e.g. "/v1/organizations/{slugOrId}"."""
    needs_auth: bool
    """True if endpoint requires authentication."""
    path_params: list[str] = field(default_factory=list)
    """Names inside {braces} in path."""
    required_query: list[str] = field(default_factory=list)
    """Query params marked required in spec."""


def _get_endpoints() -> list[Endpoint]:
    endpoints = []
    for path, methods in _SPEC["paths"].items():
        op = methods.get("get")
        if op is None:
            continue
        security = op.get("security", [])
        params = op.get("parameters", [])
        endpoints.append(Endpoint(
            path=path,
            needs_auth=any(s for s in security if s),
            path_params=re.findall(r"\{(\w+)\}", path),
            required_query=[p["name"] for p in params if p.get("in") == "query" and p.get("required")],
        ))
    return endpoints


@pytest.mark.parametrize("endpoint", _get_endpoints(), ids=lambda ep: ep.path)
def test_endpoint_matches_schema(endpoint: Endpoint, seed_ids: SeedIds, anon_client, auth_client):
    # Resolve path params
    path = endpoint.path
    for param in endpoint.path_params:
        value = seed_ids.get(param)
        if not value:
            pytest.skip(f"no {param}")
        path = path.replace(f"{{{param}}}", value)

    # Required query params
    query: dict[str, str] = {}
    for qp in endpoint.required_query:
        value = seed_ids.get(qp)
        if value:
            query[qp] = value
        else:
            pytest.skip(f"no {qp}")

    # Optional query params for better test coverage
    for qp in _EFFECTIVELY_REQUIRED.get(endpoint.path, []):
        if qp not in query:
            value = seed_ids.get(qp)
            if value:
                query[qp] = value

    # Pick client
    client: AnonClient | AuthClient
    if endpoint.needs_auth:
        if not auth_client:
            pytest.skip("no auth")
        client = auth_client
    else:
        client = anon_client

    body = client.get(path, query or None)

    response_schema = find_response_schema(_SPEC, endpoint.path)
    assert response_schema is not None, f"No response schema for {endpoint.path}"

    mismatches = find_type_mismatches(_SPEC, response_schema, body)
    assert not mismatches, "Type mismatches:\n" + "\n".join(f"  {m}" for m in mismatches)
