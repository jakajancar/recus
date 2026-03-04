from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from recus.client import AnonClient
from recus.output import console
from recus.schema.availability import (
    BookingPolicy,
    GetAvailabilityResponse,
    Pricing,
    Site,
    SiteConfig,
)
from recus.schema.sports import GetSportsResponse
from recus.sports import sport_emojis

_INDENT = " " * 4


def search(
    *,
    org: str | None = None,
    region: str | None = None,
) -> None:
    """List locations with per-slot bookable durations.

    Requires --org (slug) or --region (UUID).
    """
    if not org and not region:
        raise SystemExit("Specify --org <slug> or --region <uuid>")

    client = AnonClient()
    sport_names = _sport_lookup(client)

    params: dict[str, str] = {"publishedSites": "true"}
    if org:
        params["organizationSlug"] = org
    if region:
        params["regionId"] = region

    data = client.get("/v1/locations/availability", params=params)
    entries = GetAvailabilityResponse.model_validate(data).root

    if not entries:
        print("No locations found.")
        return

    for entry in entries:
        loc = entry.location
        if not loc.courts:
            continue

        loc_url = f"https://www.rec.us/locations/{loc.id}"
        parts = [f"[bold][link={loc_url}]{loc.name}[/link][/bold]"]
        if loc.formattedAddress:
            parts.append(loc.formattedAddress)
        if loc.hoursOfOperation:
            parts.append(loc.hoursOfOperation)

        console.print("📍 " + " · ".join(parts) + f" [dim]({loc.id})[/dim]")

        for site in loc.courts:
            sport_ids = [s.sportId for s in site.sports if s.sportId]
            emoji = sport_emojis(sport_ids)
            label_parts = [f"{emoji} [bold]{site.courtNumber}[/bold]"]
            names = [n for n in (sport_names.get(sid, "") for sid in sport_ids) if n]
            if names:
                label_parts.append(", ".join(names))

            price = _format_pricing(site.config)
            if price:
                label_parts.append(price)

            console.print(f"{_INDENT}{' · '.join(label_parts)} [dim]({site.id})[/dim]")

            if not site.availableSlots:
                if site.isInstantBookable:
                    console.print(f"{_INDENT * 2}[dim]No available slots[/dim]")
                else:
                    console.print(f"{_INDENT * 2}[dim]Not reservable online[/dim]")
                    continue
            else:
                slots_by_date = _parse_slots(site.availableSlots)
                fixed_policy = _get_fixed_slot_policy(site)
                allowed_mins = site.allowedReservationDurations.minutes

                for date_str in sorted(slots_by_date):
                    date_slots = slots_by_date[date_str]

                    if fixed_policy:
                        slot_entries = _fixed_slot_entries(date_str, date_slots, fixed_policy)
                        if not slot_entries:
                            continue
                        slot_strs = [_format_slot(hm, [dur]) for hm, dur in slot_entries]
                    else:
                        slot_strs = []
                        for hm in sorted(date_slots):
                            durations = _flexible_durations(date_slots, hm, allowed_mins)
                            if durations:
                                slot_strs.append(_format_slot(hm, durations))
                        if not slot_strs:
                            continue

                    console.print(f"{_INDENT * 2}{_format_date(date_str)}: {', '.join(slot_strs)}")

            window = site.defaultReservationWindowDays or loc.defaultReservationWindow
            release = site.reservationReleaseTimeLocal or loc.reservationReleaseTimeLocal
            if window and release:
                release_hm = datetime.strptime(release, "%H:%M:%S").strftime("%-I:%M %p").lower()
                console.print(f"{_INDENT * 2}[dim]Opens {window}d ahead at {release_hm}[/dim]")

        console.print()


# --- helpers ---


def _sport_lookup(client: AnonClient) -> dict[str, str]:
    data = client.get("/v1/sports")
    sports = GetSportsResponse.model_validate(data).root
    return {s.id: s.name for s in sports}


def _format_pricing(config: SiteConfig) -> str:
    pricing = config.pricing.default
    if not pricing:
        return ""
    if pricing.cents == 0:
        return "Free"
    return _format_price(pricing)


def _format_price(pricing: Pricing) -> str:
    dollars = pricing.cents / 100
    if pricing.type == "perHour":
        return f"${dollars:.0f}/hr" if dollars == int(dollars) else f"${dollars:.2f}/hr"
    return f"${dollars:.2f}"


def _format_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a %b %e")


def _get_fixed_slot_policy(site: Site) -> BookingPolicy | None:
    if not site.config.bookingPolicies:
        return None
    for policy in site.config.bookingPolicies:
        if policy.type == "fixed-slots" and policy.isActive:
            return policy
    return None


def _parse_slots(slots: list[str]) -> dict[str, set[str]]:
    """Group 'YYYY-MM-DD HH:MM:SS' into {date: {HH:MM, ...}}."""
    by_date: dict[str, set[str]] = defaultdict(set)
    for slot in slots:
        dt = datetime.strptime(slot, "%Y-%m-%d %H:%M:%S")
        by_date[dt.strftime("%Y-%m-%d")].add(dt.strftime("%H:%M"))
    return dict(by_date)


def _flexible_durations(
    date_slots: set[str], start_hm: str, allowed_minutes: list[int],
) -> list[int]:
    """Compute feasible durations for a start time on a flexible-booking site."""
    dt = datetime.strptime(start_hm, "%H:%M")
    return [
        dur for dur in sorted(allowed_minutes)
        if all(
            (dt + timedelta(minutes=offset)).strftime("%H:%M") in date_slots
            for offset in range(0, dur, 30)
        )
    ]


def _fixed_slot_entries(
    date_str: str, date_slots: set[str], policy: BookingPolicy,
) -> list[tuple[str, int]]:
    """Return [(start_hm, duration_min), ...] for a fixed-slot site on a date."""
    dow = datetime.strptime(date_str, "%Y-%m-%d").isoweekday()  # 1=Mon..7=Sun
    entries = []
    for slot_def in policy.slots:
        if slot_def.dayOfWeek != dow:
            continue
        start_hm = slot_def.startTimeLocal[:5]  # "07:30"
        if start_hm not in date_slots:
            continue
        # Duration = end - start
        s = datetime.strptime(slot_def.startTimeLocal, "%H:%M:%S")
        e = datetime.strptime(slot_def.endTimeLocal, "%H:%M:%S")
        dur = int((e - s).total_seconds() / 60)
        entries.append((start_hm, dur))
    return sorted(entries)


def _format_slot(hm: str, durations: list[int]) -> str:
    dur_str = "/".join(str(d) for d in durations)
    return f"[green]{hm}[/green] ({dur_str}min)"
