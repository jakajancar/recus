from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, ClassVar

import pytest

from recus.client import AnonClient, APIError, AuthClient
from recus.state import user_state


@pytest.fixture(scope="session")
def anon_client():
    return AnonClient()


@pytest.fixture(scope="session")
def auth_client() -> AuthClient | None:
    """AuthClient for the first logged-in account, or None if no account is logged in."""
    with user_state() as state:
        if not state.accounts:
            return None
        account = next(iter(state.accounts))
    return AuthClient(account)


@dataclass
class SeedIds:
    """IDs collected from seed API calls, used to fill path and query params."""

    org_slug: str | None = None
    org_id: str | None = None
    location_id: str | None = None
    site_id: str | None = None
    instructor_id: str | None = None
    user_id: str | None = None
    booking_id: str | None = None
    order_id: str | None = None
    payment_id: str | None = None
    order_item_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    _PARAM_MAP: ClassVar[dict[str, str]] = {
        "organizationSlugOrId": "org_slug",
        "locationId": "location_id",
        "siteId": "site_id",
        "instructorId": "instructor_id",
        "userId": "user_id",
        "bookingId": "booking_id",
        "orderId": "order_id",
        "paymentId": "payment_id",
        "orderItemId": "order_item_id",
        "organizationId": "org_id",
        "organizationSlug": "org_slug",
        "startDate": "start_date",
        "endDate": "end_date",
    }

    def get(self, spec_name: str) -> str | None:
        """Look up a value by OpenAPI param name (e.g. 'slugOrId' → org_slug)."""
        field_name = self._PARAM_MAP.get(spec_name)
        if field_name is None:
            return None
        return getattr(self, field_name, None)


@pytest.fixture(scope="session")
def seed_ids(anon_client, auth_client) -> SeedIds:
    """Hit key endpoints to collect IDs needed by parameterized tests."""
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=90)).isoformat()
    ids = SeedIds(start_date=today, end_date=end)

    def get(path: str, params: dict | None = None, client: AnonClient | AuthClient | None = None) -> Any:
        try:
            return (client or anon_client).get(path, params)
        except APIError:
            return None

    # Organizations
    body = get("/v1/organizations")
    if body and body.get("data"):
        ids.org_slug = body["data"][0]["slug"]
        ids.org_id = body["data"][0]["id"]

    # Availability → location_id, site_id
    if ids.org_slug:
        body = get("/v1/locations/availability", {"organizationSlug": ids.org_slug})
        if body:
            for entry in body:
                loc = entry.get("location", {})
                if not ids.location_id:
                    ids.location_id = loc.get("id")
                for c in loc.get("courts", []):
                    if c.get("availableSlots"):
                        ids.site_id = ids.site_id or c["id"]
                        ids.location_id = ids.location_id or loc["id"]
                        break
                if ids.site_id:
                    break

    # Instructors
    if ids.org_slug:
        body = get("/v1/instructors/cards/lessons", {"organizationSlug": ids.org_slug})
        if body and isinstance(body, list) and body:
            ids.instructor_id = body[0]["id"]

    # Auth-gated IDs
    if auth_client:
        body = get("/v1/users/me", client=auth_client)
        if body and isinstance(body, dict):
            ids.user_id = body["id"]

        if ids.user_id:
            body = get(f"/v1/users/{ids.user_id}/bookings", client=auth_client)
            if body and isinstance(body, dict) and body.get("data"):
                ids.booking_id = body["data"][0]["id"]

        # Order, payment, and order item from a booking
        if ids.booking_id:
            body = get("/v1/orders", {"bookingId": ids.booking_id}, client=auth_client)
            if body and isinstance(body, dict):
                order = body.get("order", {})
                ids.order_id = order.get("id")
                payments = order.get("payments", [])
                if payments:
                    ids.payment_id = payments[0]["id"]
                items = order.get("items", [])
                if items:
                    ids.order_item_id = items[0]["id"]

    return ids
