from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated

import httpx
from cyclopts import App, Parameter

from recus import cli_groups
from recus.client import AuthClient
from recus.output import console, table
from recus.schema.bookings import (
    Booking,
    GetBookingDetailResponse,
)
from recus.schema.facility_rentals import PostFacilityRentalResponse
from recus.schema.orders import PostPayACHResponse, PostPayFreeResponse
from recus.schema.sites import GetSiteDetailResponse
from recus.schema.stripe import ConfirmPaymentIntentResponse
from recus.schema.users import GetMeResponse

_STRIPE_PK = "pk_live_51MPUx4CMyY4UUjhBlgalg5uPiGdXHOWbOTEOioIXfReEeAuLviTRXhdTGvZtTnYtDm2eZonv8buTf73YKIzJHV4i00YikF7WiB"

app = App(
    name="booking",
    help="Manage bookings.",
    group=cli_groups.authd,
    default_parameter=Parameter(parse="^(?!(account|account_resolver)$)"),
)


@app.command
def create(
    site_id: Annotated[str, Parameter(help="Site UUID to book.")],
    start: Annotated[str, Parameter(help="'YYYY-MM-DD HH:MM' in the location's timezone.")],
    duration: Annotated[int, Parameter(help="Duration in minutes (e.g. 60, 90).")],
    /,
    *,
    account: str,
) -> None:
    """Create a booking. Paid bookings use the most recently added card."""
    client = AuthClient(account)

    # 1. Get site detail to resolve locationId and validate
    site = GetSiteDetailResponse.model_validate(client.get(f"/v1/sites/{site_id}")).data

    # 2. Build timestampRange (local/floating times — no timezone)
    dt = datetime.strptime(start.strip(), "%Y-%m-%d %H:%M")
    end_dt = dt + timedelta(minutes=duration)
    ts_start = dt.strftime("%Y-%m-%d %H:%M:%S")
    ts_end = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_range = f"[{ts_start}, {ts_end})"

    # 3. Create facility rental
    rental = PostFacilityRentalResponse.model_validate(
        client.post(
            "/v1/facility-rentals",
            json={
                "data": {
                    "reservation": {
                        "timestampRange": timestamp_range,
                        "locationId": site.locationId,
                        "courtIds": [site_id],
                    }
                }
            },
        )
    )

    order = rental.data.order
    assert len(order.items) == 1, f"Expected 1 order item, got {len(order.items)}"
    booking_id = order.items[0].details.bookingId

    print(f"Order {order.id} created — ${order.total / 100:.2f}")

    # 4. Pay
    if order.total == 0:
        pay = PostPayFreeResponse.model_validate(
            client.post(
                f"/v1/orders/{order.id}/pay",
                json={"data": {"payments": [{"paymentMethodType": "free", "amountCents": 0}]}},
            )
        )
        print(f"Payment: {pay.data.status}")
    else:
        # Paid booking — card-online flow then Stripe confirmation
        pay = PostPayACHResponse.model_validate(
            client.post(
                f"/v1/orders/{order.id}/pay",
                json={"data": {"payments": [{"paymentMethodType": "card-online", "amountCents": order.total}]}},
            )
        )
        gd = pay.included.payments[0].gatewayData

        if not gd.paymentMethods:
            raise SystemExit("No saved payment methods. Add a card at rec.us first.")
        match = gd.paymentMethods[0]

        print(f"Paying ${order.total / 100:.2f} with {match.card.brand} ****{match.card.last4} (pi: {gd.paymentIntentId})")

        # Confirm via Stripe API
        resp = httpx.post(
            f"https://api.stripe.com/v1/payment_intents/{gd.paymentIntentId}/confirm",
            auth=(_STRIPE_PK, ""),
            data={"payment_method": match.id, "client_secret": gd.clientSecret},
            timeout=30,
        )
        body = resp.json()
        if "error" in body:
            err = body["error"]
            raise SystemExit(f"Stripe error: {err.get('message', err.get('type', resp.status_code))}")

        confirm = ConfirmPaymentIntentResponse.model_validate(body)

        if confirm.status != "succeeded":
            raise SystemExit(f"Stripe payment failed: {confirm.status}")

        print(f"Payment: {confirm.status}")

    url = f"https://www.rec.us/app/bookings/{booking_id}"
    console.print(f"Booking: [link={url}]{booking_id}[/link]")


@app.command(name="list")
def list_bookings(*, account: str) -> None:
    """List upcoming bookings."""
    client = AuthClient(account)
    me = GetMeResponse.model_validate(client.get("/v1/users/me"))

    all_bookings = client.get_all(f"/v1/users/{me.id}/bookings")
    upcoming = [
        Booking.model_validate(b) for b in all_bookings
        if b.get("timeStatus") == "future" and b.get("canceledAt") is None
    ]

    if not upcoming:
        print("No upcoming bookings.")
        return

    rows: list[tuple[str, ...]] = []
    for b in upcoming:
        detail = GetBookingDetailResponse.model_validate(
            client.get(
                f"/v1/bookings/{b.id}",
                params={"include[]": ["reservations", "sites", "locations"]},
            )
        )
        inc = detail.included

        # Time range
        time_str = ""
        if inc.reservations:
            ts_range = inc.reservations[0].reservationTimestampRange
            if len(ts_range) == 2:
                start = datetime.strptime(ts_range[0], "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(ts_range[1], "%Y-%m-%d %H:%M:%S")
                time_str = f"{start.strftime('%Y-%m-%d %H:%M')}-{end.strftime('%H:%M')}"

        location_name = inc.locations[0].name if inc.locations else ""
        site_name = inc.sites[0].courtNumber or "" if inc.sites else ""

        url = f"https://www.rec.us/app/bookings/{b.id}"
        linked_id = f"[link={url}]{b.id}[/link]"
        rows.append((linked_id, time_str, location_name, site_name))

    table(["id", "time", "location", "site"], rows)


@app.command
def cancel(
    booking_id: Annotated[str, Parameter(help="Booking UUID to cancel.")],
    /,
    *,
    account: str,
) -> None:
    """Cancel a booking. Tries refund to original payment, then account credit, then no refund."""
    client = AuthClient(account)

    for dest in ("original_payment_methods", "account_credit"):
        try:
            print(f"Cancelling with refund → {dest}...")
            client.post(
                f"/v1/bookings/{booking_id}/cancel",
                json={"data": {"refundDestination": dest}},
            )
            print(f"Cancelled booking {booking_id}")
            return
        except SystemExit:
            continue

    raise SystemExit("Could not cancel with refund. Cancel manually at rec.us if you want to forfeit payment.")
