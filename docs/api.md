# rec.us API Reference

Base URL: `https://api.rec.us`

All endpoints below are unauthenticated unless marked with 🔒.

Responses are JSON. Errors return:

```json
{
  "correlationId": "uuid",
  "message": "Human-readable error",
  "obstructions": [],
  "type": "E_ERROR_CODE"
}
```

Common error types: `E_UNAUTHORIZED`, `E_COURT_NOT_FOUND`, `E_SECTION_NOT_FOUND`, `E_INELIGIBLE_SITE_BOOKING`, `E_INVALID_BODY`, `E_INVALID_REQUEST`, `E_FORBIDDEN`.

---

## Pagination

Some list endpoints are **paginated** (default page size 25) — callers must iterate pages to get all results. Others return the full dataset in a single response.

### Parameters

All paginated endpoints accept **either** of these equivalent param styles:

| Style | Params |
|---|---|
| Bracket (`qs`) | `pg[num]=1&pg[size]=25` |
| Flat | `page=1&pageSize=25` |

Both styles are interchangeable on every paginated endpoint. Page numbers are 1-indexed.

### Response envelopes

The response shape is fixed per endpoint (does not depend on which param style you use). Two envelope styles exist:

**`data`/`meta` envelope**:

```json
{
  "data": [ ... ],
  "meta": { "pg": { "num": 1, "size": 25, "totalResults": 49 } }
}
```

More pages exist while `pg.num * pg.size < pg.totalResults`.

**`results`/`total` envelope**:

```json
{
  "results": [ ... ],
  "total": 157
}
```

More pages exist while `page * pageSize < total`. The response does not echo back the current page number.

---

## Entity Model

```
Sport (tennis, pickleball, yoga, etc.)
Region (geographic area — "San Francisco Area", "East Bay", etc.)
Organization (city/district rec department)
├── Location (physical park/facility)
│   └── Site (bookable unit — court, field, picnic table, room, etc.)
├── Instructor (private lesson instructor)
└── Section (group class or lesson pack)
    └── Session (individual meeting within a section)

Facility Rental (a site booking)
├── Reservation (the time slot hold on a site)
└── Order (the transaction)
    └── Payment (settling the order)
```

- **Sport** — a sport or activity (e.g. Tennis, Pickleball, Yoga). Referenced by sites, instructors, and sections. Has a stable UUID.
- **Region** — a geographic area (e.g. "San Francisco Area", "East Bay"). Used to discover locations across multiple organizations. Has a lat/lng center and radius.
- **Organization** — a municipal parks & rec department (e.g. "San Francisco Rec & Park"). Has a slug for URL-friendly access. Configures which features are enabled (court reservations, coaching, lesson packs, facility rentals).
- **Location** — a park or facility with bookable sites. Has address, hours, play guidelines, and a reservation window (how many days in advance you can book).
- **Site** — a bookable unit within a location. Has an optional `type` field (e.g. `"court"`, `"field"`, `"room"`, `"picnic-table"`, `"outdoor-event-space"`, `"bounce-house"`, `"rink"`; may also be `null`). Has pricing, allowed reservation durations, and max reservation time. Some sites are not reservable (walk-up only). May support instant booking. **Note:** The API uses "site" in endpoint paths (`/v1/sites/{siteId}`) and error messages, but many response keys use the legacy name `courts` or `courtNumber` even when the site is not a court.
- **Instructor** — a coach who offers private lessons at specific locations. Has a profile, sport-specific hourly rates, and available lesson time slots.
- **Section** — a group class or lesson pack (e.g. "Pickleball Small Group Lessons - Adults"). Has a facilitator, capacity, multiple sessions over several weeks.
- **Session** — an individual meeting within a section, with a specific date/time.
- **Schedule** — the per-site time slot grid for a location on a given date. Each slot is either RESERVABLE, RESERVATION (booked), or OPEN (not reservable).
- **Facility Rental** — a site booking created via `POST /v1/facility-rentals`. Wraps a reservation and an order. Has a status (`confirmed`) and booking type (`instant`).
- **Order** — the transactional record for a booking. Created with `pending` status and a ~10 minute expiration. Must be paid (even if $0) to finalize.
- **Payment** — settles an order. Has a method type (e.g. `free`, `cardOnline`) and amount in cents.

---

## Sports

### List all sports

```
GET /v1/sports
```

Returns all sports/activities on the platform.

**Response:**

```json
[
  {
    "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "name": "Pickleball",
    "description": "A fun sport for all ages"
  },
  {
    "id": "bd745b6e-1dd6-43e2-a69f-06f094808a96",
    "name": "Tennis",
    "description": null
  }
]
```

**Notes:**
- Sport IDs are stable and referenced by `courts[].sports[].sportId` in location/availability responses (note: the `courts` key contains all site types, not just courts) and `sports[].id` in schedule responses.
- Includes non-court activities (e.g. Guitar, Yoga, Day Camp) used by the programs/sections system.

---

## Regions

### List all regions

```
GET /v1/regions
```

Returns all geographic regions.

**Response:**

```json
[
  {
    "id": "51cad8df-4985-4c09-ba5e-c7893f672c26",
    "name": "SF & Peninsula",
    "lat": "37.727239",
    "lng": "-122.400876",
    "radius": 50
  },
  {
    "id": "a9edb21b-0bc1-4eb2-802d-4f82d80f2bba",
    "name": "East Bay",
    "lat": "37.883765",
    "lng": "-121.995492",
    "radius": 50
  }
]
```

---

## Organizations

### List all organizations

```
GET /v1/organizations
```

Returns all organizations on the platform. **Paginated** (`data`/`meta` envelope — see Pagination).

**Response item:**

```json
{
  "id": "17380e28-7e02-4b52-82c5-fab18557fd7a",
  "slug": "san-francisco-rec-park",
  "name": "San Francisco Rec & Park",
  "displayName": "San Francisco Rec & Park",
  "logo": "https://prod-rec-tech-img-bucket-8656aa2.s3.us-west-1.amazonaws.com/...",
  "fullLogo": "https://...",
  "config": {
    "general": {
      "primaryState": "California",
      "primaryTimezone": "America/Los_Angeles"
    }
  }
}
```

### Get organization detail

```
GET /v1/organizations/{slugOrId}
```

**Path params:**
- `slugOrId` — organization slug (e.g. `san-francisco-rec-park`) or UUID

**Response:**

```json
{
  "id": "17380e28-7e02-4b52-82c5-fab18557fd7a",
  "slug": "san-francisco-rec-park",
  "name": "San Francisco Rec & Park",
  "description": "Official SF organization",
  "logo": "https://...",
  "fullLogo": "https://...",
  "config": {
    "tabs": {
      "coaching": { "order": 2 },
      "programs": { "name": "Lesson Packs", "order": 3 },
      "locations": { "name": "Court Reservations", "order": 1 },
      "facilityRentals": { "enabled": false },
      "membershipsAndPasses": { "enabled": false }
    },
    "banners": {
      "pages": {
        "/locations/{locationId}": "Banner text (markdown)..."
      }
    },
    "general": {
      "primaryState": "California",
      "primaryTimezone": "America/Los_Angeles"
    },
    "lessons": {
      "restrictions": {
        "allowedDurations": { "minutes": [30, 60, 90] },
        "maxWeeklyBookings": 15
      }
    }
  },
  "activityOrCategoryOrder": []
}
```

**`config.tabs`** controls which features are enabled for the organization. A tab with `"enabled": false` is disabled. Possible tabs:
- `locations` — court reservations (renamed per org, e.g. "Court Reservations", "Sport Facility Rentals")
- `coaching` — private lessons with instructors
- `programs` — group classes / lesson packs
- `facilityRentals` — picnic/event space rentals
- `membershipsAndPasses` — membership programs

---

## Locations

### Get location detail

```
GET /v1/locations/{locationId}
```

**Path params:**
- `locationId` — UUID

**Query params:**
- `publishedSites` — `"true"` to include published site info (optional)

**Note:** The response nests sites under a `courts` key, but this array contains **all** site types (courts, fields, rooms, picnic tables, etc.), not just courts. Similarly, `courtNumber` is the display name for any site type (e.g. `"Court 1"`, `"Picnic Table A"`, `"Room 201"`).

**Response:**

```json
{
  "location": {
    "id": "95745483-6b38-4e99-8ba2-a3e23cda8587",
    "name": "Dolores",
    "description": "TBD",
    "formattedAddress": "3753 18th St, San Francisco, CA 94114, USA",
    "lat": "37.76100510000001",
    "lng": "-122.4271707",
    "placeId": "ChIJ_c7oyBl-j4ARczOfJmf4QzU",
    "hoursOfOperation": "7:00am to 9:00pm",
    "timezone": "America/Los_Angeles",
    "playGuidelines": "Markdown string with reservation policy, court info, etc.",
    "accessInfo": "Courts are unlocked...",
    "gettingThereInfo": "The courts are located along the north side...",
    "defaultReservationWindow": 7,
    "reservationReleaseTimeLocal": "08:00:00",
    "reservationBuffer": 0,
    "privateLessonReservationWindow": 0,
    "organizationId": "17380e28-7e02-4b52-82c5-fab18557fd7a",
    "images": {
      "detail": "https://...",
      "thumbnail": "https://...",
      "mainGallery": "https://...",
      "smallGallery1": "https://...",
      "smallGallery2": "https://..."
    },
    "organization": {
      "id": "17380e28-7e02-4b52-82c5-fab18557fd7a",
      "name": "San Francisco Rec & Park",
      "slug": "san-francisco-rec-park"
    },
    "courts": [
      {
        "id": "8ad0975e-9498-4bca-8832-26368ca54de7",
        "courtNumber": "Court 1",
        "maxReservationTime": "01:30:00",
        "noReservationText": null,
        "allowPrivateLessons": false,
        "type": "court",
        "capacity": null,
        "description": null,
        "bufferMinutesBetweenReservations": 0,
        "allowedReservationDurations": {
          "minutes": [30, 60, 90]
        },
        "config": {
          "pricing": {
            "default": {
              "type": "perHour",
              "cents": 500
            }
          }
        },
        "sports": [
          {
            "id": "65751cfa-31f5-4e0f-a5db-5bc2079f4ac0",
            "courtId": "8ad0975e-9498-4bca-8832-26368ca54de7",
            "sportId": "bd745b6e-1dd6-43e2-a69f-06f094808a96",
            "price": 0,
            "currency": "USD"
          }
        ],
        "images": { "map": [], "mainGallery": [] },
        "amenities": { "amenityTagIds": [] }
      }
    ],
    "tags": [],
    "regions": []
  }
}
```

**Notes:**
- `courts[]` — despite the key name, contains all site types. Each entry has a `type` field (e.g. `"court"`, `"field"`, `"room"`, or `null`).
- `courts[].courtNumber` — the display name for any site (e.g. `"Court 1"`, `"Field A"`, `"Room 201"`), despite the field name.
- `courts[].noReservationText` — if set (e.g. `"Not Reservable"`), the site is walk-up only.
- `courts[].availableSlots` — bookable start times as `"YYYY-MM-DD HH:MM:SS"` strings in the location's timezone. Covers the upcoming reservation window. Not shown in the example above but always present in the response.
- `courts[].allowedReservationDurations` — the set of durations this site supports.
- `courts[].config.bookingPolicies` — optional. When present with `type: "fixed-slots"` and `isActive: true`, the site uses pre-defined time blocks. Not shown in the example above. See "Computing per-slot durations client-side" below.
- `courts[].isInstantBookable` — whether the site can be booked directly. Not shown in the example above but always present.
- `courts[].sports[].sportId` — references a global sport. The sport **name** is not included here; it appears in the schedule endpoint. Known sport IDs:
  - `bd745b6e-1dd6-43e2-a69f-06f094808a96` — Tennis
- `defaultReservationWindow` — how many days in advance reservations open (e.g. 7 = one week ahead).
- `reservationReleaseTimeLocal` — the local time when new reservation slots become available (e.g. `"08:00:00"` = 8 AM).
- `playGuidelines` — detailed markdown with reservation rules, site assignments, hours, etc. Very useful for understanding location-specific policies.

---

## Availability & Schedule — Endpoint Comparison

Four endpoints return time slot / availability data. They overlap significantly but each has unique fields. The rec.us frontend uses them in different contexts:

- **Location search** (`/locations` page) — calls `GET /v1/locations/availability` to discover which locations have open slots across an org or region.
- **Location detail / court booking** (`/locations/[locationId]` page) — calls `GET /v1/locations/{id}` (with `publishedSites=true`) for site metadata + available start times, and `GET /v1/locations/{id}/schedule` for the visual day grid. Per-slot durations are computed client-side from `availableSlots` + `allowedReservationDurations` (see below). The booking flow happens inline on this page.
- **Facility rental booking** (`/sites/[siteId]` page) — calls `GET /v1/sites/{id}/availability` for per-slot duration options. This page is reached from the **Facility Rentals tab** on the org page (`/organizations/[slug]?tab=facilityRentals`), which lists sites via `GET /v1/sites?organizationId={id}`. Each site card links to `/sites/{siteId}`. This flow is used for non-court site types (picnic tables, rooms, event spaces, bounce houses, etc.).

The main court reservation flow (`/locations/[locationId]`) **never calls** `GET /v1/sites/{id}/availability` — it computes equivalent data client-side. Only the standalone `/sites/[siteId]` page uses that endpoint.

| | `GET /v1/locations/{id}` | `GET /v1/locations/availability` | `GET /v1/sites/{id}/availability` | `GET /v1/locations/{id}/schedule` |
|---|---|---|---|---|
| **Intent** | "What can I book here?" — single location with bookable start times per site | "Where can I play?" — cross-location discovery of bookable start times | "How long can I book?" — per-slot duration options for a specific site | "What does the day look like?" — full slot grid with bookings, open hours, and reservable slots |
| **Frontend usage** | Location detail page — site metadata + booking flow | Location search/map page | `/sites/[siteId]` page (facility rentals only) | Location detail page — visual schedule grid |
| **Scope** | Single location, all sites | Multi-location (filter by org, region, or lat/lng) | Single site | Single location, all sites |
| Site ID (UUID) | Yes, per site (in `courts[].id`) | Yes, per site (in `courts[].id`) | N/A (you provide it) | Only indirectly, via `reservations[].courts[]` (booked slots only; key name is misleading) |
| Available start times | Yes (`courts[].availableSlots`) | Yes (`courts[].availableSlots`) | Yes (keys of `data[date]`) | No (has RESERVABLE ranges, not individual start times) |
| Sport names | No (only `sportId`) | No (only `sportId`) | No | Yes (`sports[].name`) |
| All slot states | No — available start times only | No — available start times only | No — available start times only | Yes — RESERVABLE, RESERVATION, OPEN |
| Who booked each slot | No | No | No | Yes — `users` dict with names, skill levels |
| Per-slot available durations | No (can be computed client-side — see below) | No (can be computed client-side — see below) | Yes (`availableDurationsMinutes` per time) | No |
| Booking policies | Yes (`courts[].config.bookingPolicies`) | Yes (`courts[].config.bookingPolicies`) | No | No |
| `allowedReservationDurations` | Yes, per site | Yes, per site | No | No |
| Pricing | Yes, per site (`config.pricing`) | Yes, per site (`config.pricing`) | No | Only on booked reservations (`reservationCost`) |
| `isInstantBookable` | Yes, per site | Yes, per site | No | No |
| Multi-location | No | Yes | No | No |
| Date range | Automatic (reservation window, typically 7 days) | Automatic (reservation window, typically 7 days) | Automatic (reservation window, typically 7 days) | Explicit `startDate`/`endDate` params |

### Computing per-slot durations client-side

`GET /v1/sites/{id}/availability` returns `availableDurationsMinutes` per time slot, but requires one request per site — impractical for multi-site views. Both `GET /v1/locations/{id}` and `GET /v1/locations/availability` return enough data to compute equivalent durations client-side (this is what the rec.us frontend does for court reservations on the location detail page).

Each site (in `courts[]`) provides three relevant fields:
- `availableSlots` — bookable start times as `"YYYY-MM-DD HH:MM:SS"` strings
- `allowedReservationDurations.minutes` — e.g. `[30, 60, 90]`
- `config.bookingPolicies[]` — optional; when present with `type: "fixed-slots"` and `isActive: true`, the site uses pre-defined time blocks

**Fixed-slot sites** (active `bookingPolicies` with `type: "fixed-slots"`):

The `bookingPolicies[].slots` array defines the valid time blocks per day of week (`dayOfWeek` 1=Mon…7=Sun). Each slot has `startTimeLocal` and `endTimeLocal`. For each block whose `startTimeLocal` (truncated to `HH:MM`) appears in `availableSlots` on a matching day-of-week, the only available duration is `endTimeLocal - startTimeLocal`. The `allowedReservationDurations` field is ignored — it contains a stale superset.

Note: `availableSlots` for fixed-slot sites includes every 30-minute tick within the open range (e.g. `07:30`, `08:00`, `08:30` for a 07:30–09:00 block), but only the block start times are valid booking starts.

**Flexible-booking sites** (no active `bookingPolicies`, or `isActive: false`):

For each start time in `availableSlots`, check which durations from `allowedReservationDurations.minutes` are feasible by verifying that all consecutive 30-minute sub-slots exist:

```
for each duration in allowedReservationDurations.minutes (ascending):
    feasible = true
    for offset in 0, 30, 60, ... (duration - 30):
        if (startTime + offset) not in availableSlots for that date:
            feasible = false; break
    if feasible: include duration
```

For example, with `allowedReservationDurations: [30, 60, 90]` and `availableSlots` containing `17:00, 17:30, 18:00` but not `18:30`:
- At 17:00: `[30, 60, 90]` (17:00, 17:30, 18:00 all present)
- At 17:30: `[30, 60]` (17:30, 18:00 present; 18:30 missing)
- At 18:00: `[30]` (18:00 present; 18:30 missing)

This computation produces results identical to `GET /v1/sites/{id}/availability`.

---

## Schedule

### Get schedule

```
GET /v1/locations/{locationId}/schedule?startDate={YYYY-MM-DD}[&endDate={YYYY-MM-DD}]
```

Returns the schedule for **all sites** at a location for the given date range.

**Path params:**
- `locationId` — UUID

**Query params:**
- `startDate` — required, format `YYYY-MM-DD`
- `endDate` — optional, format `YYYY-MM-DD` (defaults to same as startDate)

**Response:**

```json
{
  "dates": {
    "20260301": [
      {
        "courtNumber": "Court 1",
        "sports": [
          { "id": "bd745b6e-1dd6-43e2-a69f-06f094808a96", "name": "Tennis" }
        ],
        "schedule": {
          "07:00, 07:30": {
            "referenceType": "OPEN",
            "referenceLabel": "Not Reservable"
          },
          "07:30, 09:00": {
            "referenceType": "RESERVATION",
            "referenceId": "bc5ddf13-26bb-4fec-9077-a3d47995b652"
          },
          "12:00, 13:30": {
            "referenceType": "RESERVABLE"
          },
          "21:00, 22:00": {
            "referenceType": "OPEN",
            "referenceLabel": "Not Reservable"
          }
        }
      },
      {
        "courtNumber": "Court A",
        "sports": [
          { "id": "...", "name": "Pickleball" }
        ],
        "schedule": { "...": "..." }
      }
    ]
  },
  "reservations": {
    "bc5ddf13-26bb-4fec-9077-a3d47995b652": {
      "id": "bc5ddf13-26bb-4fec-9077-a3d47995b652",
      "reservationType": "court-reservation",
      "reservationCost": 750,
      "reservationCostCurrency": "USD",
      "guestPrice": 750,
      "capacity": 1,
      "paid": true,
      "visibility": "public",
      "doNotMarket": false,
      "groupsOnly": null,
      "classId": null,
      "sessionId": null,
      "instructorId": null,
      "facilityRentalId": "some-uuid",
      "linkedReservationId": "some-uuid",
      "locationId": "95745483-6b38-4e99-8ba2-a3e23cda8587",
      "users": ["user-uuid"],
      "courts": ["court-uuid"]
    }
  },
  "users": {
    "user-uuid": {
      "id": "user-uuid",
      "firstName": "K",
      "lastName": "N",
      "image": null,
      "skillLevel": "first-timer",
      "primarySportId": null
    }
  },
  "instructors": {},
  "classes": {},
  "sessions": {},
  "facilityRentals": {}
}
```

**Schedule slot keys** are formatted as `"HH:MM, HH:MM"` (start time, end time in 24h local time).

**`referenceType` values:**
| Value | Meaning |
|---|---|
| `RESERVABLE` | Open slot — can be booked |
| `RESERVATION` | Already booked — `referenceId` links to the `reservations` dict |
| `OPEN` | Not reservable — `referenceLabel` explains why (e.g. "Not Reservable" for walk-up courts or outside bookable hours) |

**`reservations` dict:** Keyed by reservation UUID. Contains cost (in cents), who booked it (`users[]`), which site (`courts[]` — key name is misleading), and whether it's a regular reservation, lesson, or class.

**`users` dict:** Keyed by user UUID. Only shows first initial and last initial for privacy. Includes `skillLevel` (e.g. "first-timer", "beginner", "intermediate", "advanced").

**`instructors`, `classes`, `sessions`, `facilityRentals` dicts:** Populated when the schedule includes instructor lessons, group classes, or facility rentals. Empty for pure reservation schedules.

**Note:** The schedule response uses `courtNumber` as the display name for each site entry, even for non-court site types. There is no site UUID in the schedule's per-site entries — only `courtNumber` and `sports`. Site UUIDs appear only in `reservations[].courts[]` for booked slots.

---

## Availability (multi-location)

### Get available slots across locations

```
GET /v1/locations/availability?regionId={regionId}
GET /v1/locations/availability?organizationSlug={slug}
```

Returns all locations with their sites and available time slots. This is the multi-location equivalent of the schedule endpoint — instead of detailed per-slot status for one location, it returns a flat list of bookable slot timestamps across many locations at once. Also serves as the only way to list locations for a specific organization (the `GET /v1/locations` endpoint does not support org filtering).

**Query params (at least one required):**
- `regionId` — UUID of a region
- `organizationSlug` — organization slug (e.g. `san-francisco-rec-park`)
- `latitude`, `longitude` — geo filter (optional)
- `publishedSites` — `"true"` (optional)

**Response:**

```json
[
  {
    "distance": null,
    "location": {
      "id": "81cd2b08-8ea6-40ee-8c89-aeba92506576",
      "name": "Alice Marble",
      "formattedAddress": "1200 Greenwich St, San Francisco, CA 94109, USA",
      "lat": "37.7977...",
      "lng": "-122.4179...",
      "hoursOfOperation": "7:00am to 7:30pm",
      "timezone": "America/Los_Angeles",
      "organizationId": "17380e28-...",
      "defaultReservationWindow": 7,
      "reservationReleaseTimeLocal": "08:00:00",
      "playGuidelines": "...",
      "images": { "thumbnail": "https://..." },
      "courts": [
        {
          "id": "court-uuid",
          "courtNumber": "Court 1",
          "maxReservationTime": "01:30:00",
          "type": "court",
          "sports": [
            { "id": "...", "sportId": "bd745b6e-..." }
          ],
          "config": {
            "pricing": { "default": { "type": "perHour", "cents": 500 } }
          },
          "allowedReservationDurations": { "minutes": [30, 60, 90] },
          "availableSlots": [
            "2026-03-02 07:30:00",
            "2026-03-02 08:00:00",
            "2026-03-02 08:30:00",
            "2026-03-02 09:00:00"
          ],
          "slots": [
            {
              "type": "PRIVATE",
              "openFrom": "07:30:00",
              "openTo": "19:30:00",
              "dayOfWeek": 1
            }
          ]
        }
      ]
    }
  }
]
```

**Notes:**
- `courts[]` — despite the key name, contains all site types (courts, fields, rooms, picnic tables, etc.). Each entry has a `type` field.
- `availableSlots` — flat list of bookable start times as `"YYYY-MM-DD HH:MM:SS"` strings in the location's timezone. Covers the upcoming reservation window (typically 7 days).
- `slots` — the recurring weekly schedule template (which hours are open for booking on each day of week). `dayOfWeek` uses 0=Sunday, 1=Monday, etc.
- `distance` — populated when filtering by lat/lng, otherwise null.
- `sports[].sportId` — references the global sport ID but does **not** include the sport name. Use the schedule endpoint or cross-reference with known sport IDs.
- Only locations with at least one site are returned. Locations with zero available slots are still included (check `availableSlots` length).

**Example: Find all SF locations with open pickleball slots:**

```bash
curl -s 'https://api.rec.us/v1/locations/availability?organizationSlug=san-francisco-rec-park' | \
  jq '[.[] | {name: .location.name, courts: [.location.courts[] | select(.availableSlots | length > 0) | {court: .courtNumber, slots: (.availableSlots | length)}]} | select(.courts | length > 0)]'
```

---

## Instructors

### List instructors with available lessons

```
GET /v1/instructors/cards/lessons?organizationSlug={slug}
GET /v1/instructors/cards/lessons?locationId={locationId}
```

**Query params (at least one required):**
- `organizationSlug` — filter by organization
- `locationId` — filter by location
- `regionId` — filter by region (optional)
- `latitude`, `longitude` — geo filter (optional)

**Response:**

```json
[
  {
    "id": "415856ca-7fe0-4473-aa7e-5ea145bd871c",
    "firstName": "Veronique",
    "lastName": "Chalhoub",
    "fullName": "Veronique Chalhoub",
    "shortDescription": "Usually available: Weekdays 10:30AM-6PM, Saturdays 10:30AM-6PM",
    "profileImage": "https://...",
    "tags": [],
    "config": {
      "offersLessonPacks": true,
      "doNotMarketForLessons": false
    },
    "sports": [
      {
        "id": "bd745b6e-1dd6-43e2-a69f-06f094808a96",
        "name": "Tennis",
        "hourlyRate": 98
      }
    ],
    "certifications": [],
    "lessons": [
      {
        "id": "9efc7f51-2c27-47f5-b622-6fcdcb20c89c",
        "reservationTimestampRange": {
          "from": { "date": "2026-03-02", "time": "13:00:00" },
          "to": { "date": "2026-03-02", "time": "14:00:00" },
          "inclusive": { "lower": true, "upper": false }
        },
        "classId": null,
        "classRecommendedLevel": null,
        "className": null,
        "sport": {
          "id": "bd745b6e-1dd6-43e2-a69f-06f094808a96",
          "name": "Tennis"
        },
        "location": {
          "id": "3552b6f7-e7bd-4334-9e4a-731b015447e0",
          "name": "Helen Wills"
        }
      }
    ]
  }
]
```

**`lessons[]`** — upcoming available time slots for booking a private lesson with this instructor. Each has a time range, sport, and location.

### Get instructor detail

```
GET /v1/instructors/{instructorId}
```

**Response:**

```json
{
  "id": "415856ca-7fe0-4473-aa7e-5ea145bd871c",
  "userId": "5312b05a-230b-4d74-a30e-aa3f5f62f8cc",
  "shortDescription": "Usually available: Weekdays 10:30AM-6PM...",
  "longBio": "Markdown string with full bio, availability, pricing...",
  "canTeachPrivateLessons": true,
  "isPro": false,
  "tags": [],
  "certifications": [],
  "images": {
    "instructorAvatar80x80": "https://...",
    "instructor152x89": "https://...",
    "instructor152x240": "https://...",
    "instructor240x140": "https://..."
  },
  "config": {
    "doNotMarketForLessons": false
  },
  "user": {
    "id": "5312b05a-230b-4d74-a30e-aa3f5f62f8cc",
    "firstName": "Veronique",
    "lastName": "Chalhoub"
  },
  "sports": [
    {
      "id": "bd745b6e-1dd6-43e2-a69f-06f094808a96",
      "name": "Tennis",
      "hourlyRate": 98
    }
  ],
  "instructorLocations": [
    {
      "id": "bcea8747-...",
      "instructorId": "415856ca-...",
      "locationId": "16fdf80f-...",
      "hourlyRate": 89,
      "sportId": "bd745b6e-..."
    }
  ]
}
```

**`instructorLocations[]`** — which locations this instructor teaches at, with per-location hourly rates (may differ from the base rate in `sports[]`).

---

## Discovery / Programmed Sections

### List available programs and group classes

```
GET /v1/discovery/programmed?organizationId={id}&startDate={YYYY-MM-DD}&endDate={YYYY-MM-DD}
GET /v1/discovery/programmed?locationId={id}&startDate={YYYY-MM-DD}&endDate={YYYY-MM-DD}
```

**Query params (at least one of organizationId/locationId/regionId/instructorId required):**
- `organizationId` — UUID
- `locationId` — UUID
- `regionId` — UUID (optional)
- `instructorId` — UUID (optional)
- `sportIds` — filter by sport (optional)
- `startDate` — required, format `YYYY-MM-DD`
- `endDate` — required, format `YYYY-MM-DD`

**Response:**

```json
[
  {
    "id": "850b8843-f2e5-40ea-a709-4c3e98a9af5c",
    "name": "Pickleball Small Group Lessons - Adults",
    "timezone": "America/Los_Angeles",
    "recommendedLevel": "all",
    "sportId": "bd745b6e-1dd6-43e2-a69f-06f094808a96",
    "sportName": "Pickleball",
    "locationName": "Rossi",
    "capacity": 4,
    "participantCount": 0,
    "facilitators": [
      {
        "id": "instructor-uuid",
        "firstName": "Jane",
        "lastName": "Doe",
        "imageUrl": "https://..."
      }
    ],
    "sessions": [
      { "timestampRange": ["2026-03-01 12:00:00", "2026-03-01 13:00:00"] },
      { "timestampRange": ["2026-03-08 12:00:00", "2026-03-08 13:00:00"] },
      { "timestampRange": ["2026-03-15 12:00:00", "2026-03-15 13:00:00"] },
      { "timestampRange": ["2026-03-22 12:00:00", "2026-03-22 13:00:00"] }
    ]
  }
]
```

**Notes:**
- `capacity` — max participants. `participantCount` — currently enrolled. Available spots = `capacity - participantCount`.
- `sessions[]` — individual meeting dates/times. Timestamps are in the section's timezone.
- `recommendedLevel` — skill level (e.g. "all", "beginner", "intermediate", "advanced").
- Types of sections include lesson packs (1:1, capacity=1), small group lessons (capacity=4), and other programs.

---

## Sections

### Get section detail

```
GET /v1/sections/{sectionId}
```

Returns detailed information about a specific section/program.

**Note:** Section IDs from the discovery endpoint may not resolve here — the discovery endpoint returns a denormalized view that may use different identifiers.

### Get section add-ons

```
GET /v1/sections/{sectionId}/addons
```

Returns available add-ons for a section.

### Join section waitlist 🔒

```
POST /v1/sections/{sectionId}/waitlist
```

Requires authentication. Body: `{ "data": { ... } }`.

---

## Sites

Sites are the bookable units within a location. The API uses "site" in endpoint paths (`/v1/sites/{siteId}`), but legacy response keys use `courts` and `courtNumber` (see Locations section). The `courts[].id` from the location endpoint is the same as the `siteId` used here.

### List sites for an organization

```
GET /v1/sites?organizationId={id}
```

Returns facility-rental sites for a given organization. **Paginated** (`results`/`total` envelope — see Pagination).

**Only returns non-court site types** (picnic tables, bounce houses, gyms, outdoor event spaces, etc.). Courts, fields, and rinks are **not** included — those are accessed exclusively through the location endpoints (`GET /v1/locations/{id}` and `GET /v1/locations/availability`). Organizations that only have courts (e.g. `san-francisco-rec-park`) return `total: 0`.

**Query params:**
- `organizationId` — UUID (required)

**Response items** have the same shape as `GET /v1/sites/{siteId}` `.data`.

### Get site detail

```
GET /v1/sites/{siteId}
```

Returns detailed information about a specific site, including whether it supports instant booking.

**Response:**

```json
{
  "data": {
    "id": "99b7129e-5ed4-4fd8-aba2-fee1683310bb",
    "courtNumber": "A",
    "capacity": 0,
    "isInstantBookable": true,
    "noReservationText": null,
    "locationId": "38a201f0-4fb1-4991-8e72-db8a9495319e",
    "locationName": "Granada Park",
    "config": {
      "pricing": { "default": { "type": "perHour", "cents": 0 } },
      "deposits": {},
      "bookingPolicies": [
        {
          "type": "fixed-slots",
          "isActive": true,
          "slots": [
            { "dayOfWeek": 1, "startTimeLocal": "07:30:00", "endTimeLocal": "09:00:00" },
            { "dayOfWeek": 1, "startTimeLocal": "09:00:00", "endTimeLocal": "10:30:00" }
          ]
        }
      ]
    },
    "allowedReservationDurations": { "minutes": [30, 60, 90, 120] },
    "maxReservationTime": "02:00:00",
    "images": { "map": [], "mainGallery": [] },
    "descriptionMd": null,
    "rulesMd": null
  }
}
```

**Notes:**
- `courtNumber` — the display name (e.g. `"A"`, `"Court 1"`, `"Picnic Table 3"`), despite the field name.
- `capacity` — 0 means no cap on attendees.
- `isInstantBookable` — if `true`, the site can be booked directly via the facility-rentals endpoint. If `false`, the site may require a request/approval flow.
- `noReservationText` — if set (e.g. `"Not Reservable"`), the site is walk-up only.
- `config.bookingPolicies[]` — optional. When present with `type: "fixed-slots"`, the site uses pre-defined time blocks instead of flexible durations. The `timestampRange` in a facility-rental request **must** exactly match one of these slot boundaries, or the API will reject with `"The reservation violates the site's booking policy"`. `dayOfWeek` uses 1=Monday through 7=Sunday. If no `bookingPolicies` are present, the site uses flexible booking with `allowedReservationDurations`.

### Get site availability

```
GET /v1/sites/{siteId}/availability
```

Returns available dates and time slots for a specific site.

**Response:**

```json
{
  "data": {
    "2026-03-05": {
      "08:00:00": { "availableDurationsMinutes": [30, 60, 90, 120] },
      "08:30:00": { "availableDurationsMinutes": [30, 60, 90] },
      "13:00:00": { "availableDurationsMinutes": [30, 60, 90, 120] },
      "13:30:00": { "availableDurationsMinutes": [30, 60, 90] }
    }
  }
}
```

**Notes:**
- Keys are dates (`YYYY-MM-DD`), values are objects keyed by start time (`HH:MM:SS`).
- Each time slot lists which durations (in minutes) are available starting at that time.
- This endpoint is used by the frontend to populate the time and duration pickers.

### Get site instant booking configuration

```
GET /v1/sites/{siteId}/instant-booking-configuration
```

Returns the instant booking configuration for a site, if one exists. Returns 404 if not configured.

### Get site add-ons

```
GET /v1/sites/{siteId}/addons
```

Returns add-ons available when booking a specific site. Response: `{ "data": [] }`.

---

## Authentication

Authenticated endpoints (marked 🔒) require a Firebase Auth ID token passed as a Bearer token.

**Firebase project:** `rec-prod`
**Firebase Web API key:** `AIzaSyCp6DCwnx-6GwkMyI2G1b8ixYs4AXZc-7s`

### Sign in with email/password

```
POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCp6DCwnx-6GwkMyI2G1b8ixYs4AXZc-7s
```

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "password",
  "returnSecureToken": true
}
```

**Response:**

```json
{
  "localId": "1N78WJBXjdU1avTCTx9z1JkFWMv1",
  "email": "user@example.com",
  "displayName": "",
  "idToken": "eyJhbGciOi...",
  "refreshToken": "AMf-vBx...",
  "expiresIn": "3600"
}
```

The `idToken` is used as the Bearer token for all authenticated API calls:

```
Authorization: Bearer {idToken}
```

Tokens expire after 1 hour. Use the `refreshToken` with the Firebase token refresh endpoint to obtain a new `idToken`.

---

## Authenticated Endpoints 🔒

The following endpoints require a valid session/auth token (see Authentication section above).

### User

```
GET    /v1/users/me                              → current user profile
GET    /v1/users/{userId}/household               → user's household members
GET    /v1/users/{userId}/groups                   → user's group memberships
GET    /v1/users/{userId}/payment-methods           → saved payment methods
GET    /v1/users/{userId}/claimables/check          → check claimable items
POST   /v1/users/signup/validate                   → validate signup data
POST   /v1/users/send-verification                  → send verification code
POST   /v1/users/{userId}/payment-method-setup      → get Stripe setup intent + saved cards (see below)
```

#### Get saved payment methods (Stripe)

```
POST /v1/users/{userId}/payment-method-setup
```

Returns a Stripe SetupIntent and the user's saved payment methods for a given organization. This is how you discover saved card IDs (`pm_...`) needed for the card payment flow.

**Request body:**

```json
{
  "data": {
    "organizationId": "17380e28-7e02-4b52-82c5-fab18557fd7a"
  }
}
```

**Response:**

```json
{
  "data": {
    "provider": "stripe",
    "setupIntentId": "seti_1T5tqjCMyY4UUjhB8p5JyVDt",
    "clientSecret": "seti_1T5tqjCMyY4UUjhB..._secret_...",
    "paymentMethods": [
      {
        "id": "pm_1Sygm4CMyY4UUjhBOhNeoApv",
        "card": {
          "brand": "visa",
          "exp_month": 1,
          "exp_year": 2031,
          "last4": "7510"
        }
      }
    ]
  }
}
```

**Notes:**
- `paymentMethods[].id` — the Stripe PaymentMethod ID (e.g. `pm_...`). Used when confirming a PaymentIntent via the Stripe API.
- `setupIntentId` / `clientSecret` — a Stripe SetupIntent for adding new payment methods (not needed for paying with an existing saved card).
- `organizationId` is required because payment methods are scoped per Stripe Connect account (each organization has its own).

### Site Reservations (Facility Rentals)

```
POST   /v1/facility-rentals                        → create a site reservation
```

**Request body:**

```json
{
  "data": {
    "reservation": {
      "timestampRange": "[2026-03-05 13:00:00, 2026-03-05 14:00:00)",
      "locationId": "38a201f0-4fb1-4991-8e72-db8a9495319e",
      "courtIds": ["99b7129e-5ed4-4fd8-aba2-fee1683310bb"]
    }
  }
}
```

**Notes:**
- `timestampRange` — PostgreSQL-style range: `[` = inclusive start, `)` = exclusive end. Times are in the location's timezone.
- `courtIds` — array of site UUIDs to reserve. Despite the name, accepts any site type (court, field, room, etc.). Typically one site per reservation.
- Do **not** include `attendeeCount` for sites with `capacity: 0` (uncapped), or the API will reject with `"Attendee count exceeds site capacity"`.
- The site must have `isInstantBookable: true` (check via `GET /v1/sites/{siteId}`).

**Response (201 Created):**

```json
{
  "data": {
    "order": {
      "id": "6334b6ee-dab8-4bd7-ba56-c38c51df3a16",
      "flow": "cart",
      "status": "pending",
      "timeRemainingMs": 599523,
      "expiresAt": "2026-02-28T19:09:37.457Z",
      "currency": "USD",
      "subtotal": 0,
      "total": 0,
      "customer": {
        "id": "user-uuid",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com"
      },
      "organization": {
        "id": "org-uuid",
        "name": "Town of Corte Madera"
      },
      "items": [
        {
          "id": "item-uuid",
          "name": "Court Reservation: A",
          "basePrice": 0,
          "finalPrice": 0,
          "productType": "site-reservation",
          "details": {
            "bookingId": "booking-uuid",
            "reservationId": "reservation-uuid",
            "reservationType": "court-reservation",
            "timestampRange": ["2026-03-05 13:00:00", "2026-03-05 14:00:00"],
            "location": { "id": "location-uuid", "name": "Granada Park" },
            "sites": [{ "id": "court-uuid", "name": "A", "type": "court" }]
          }
        }
      ]
    },
    "facilityRental": {
      "id": "facility-rental-uuid",
      "status": "confirmed",
      "bookingType": "instant"
    }
  }
}
```

**Important:** The order is created with `status: "pending"` and has an expiration timer (~10 minutes). You must complete the order by calling `POST /v1/orders/{orderId}/pay` before it expires, even for free ($0) reservations.

### Orders & Checkout

```
GET    /v1/orders/current                          → current active order
GET    /v1/orders/{orderId}                        → order detail (wraps response in "order" key)
GET    /v2/orders/{orderId}                        → order detail v2 (supports include[]=installments)
GET    /v1/orders/{orderId}/items                  → order line items
GET    /v1/orders/{orderId}/transaction-events      → payment history
POST   /v1/orders/{orderId}/pay                    → submit payment (see below)
POST   /v1/orders/{orderId}/apply-discount          → apply discount/promo code
DELETE /v1/orders/{orderId}                        → delete/cancel a pending order
DELETE /v1/order-items/{orderItemId}               → remove an item from an order
GET    /v1/orders?bookingId={bookingId}            → orders by booking
```

#### Submit payment

```
POST /v1/orders/{orderId}/pay
```

**Request body:**

```json
{
  "data": {
    "payments": [
      {
        "paymentMethodType": "free",
        "amountCents": 0
      }
    ]
  }
}
```

**Payment method types:**

| Type | Use case | API-callable? |
|---|---|---|
| `free` | $0 reservations (`amountCents` must be `0`) | Yes |
| `ACH` | Triggers Stripe PaymentIntent for card payment | Yes (see below) |
| `cardOnline` | Used by the web frontend only | **No** — rejected with `E_INVALID_BODY` |
| `organizationCredit` | Org credit balance | Untested |
| `check` | Check (also requires `checkNumber` field) | Admin only |
| `cash` | Cash payment | Admin only (`E_FORBIDDEN` for consumers) |
| `cardPresent` | In-person card (also requires `providerReaderId` field) | Admin only |
| `giftCard` | Gift card (also requires `storedValueAccountCode` field) | Untested |
| `scholarship` | Scholarship (also requires `storedValueAccountCode` field) | Untested |

**Response for `free` (200 OK — immediate settlement):**

```json
{
  "data": {
    "id": "transaction-event-uuid",
    "type": "payment",
    "status": "succeeded",
    "orderId": "order-uuid",
    "settledAt": "2026-02-28T19:01:55.059Z"
  }
}
```

#### Paying with a saved card (Stripe flow)

The `cardOnline` payment type is rejected by the API with `E_INVALID_BODY` when called directly. To pay with a saved card via the API, use `paymentMethodType: "ACH"` instead — this creates a Stripe PaymentIntent that you then confirm with the Stripe API using a saved card.

**Stripe publishable key:** `pk_live_51MPUx4CMyY4UUjhBlgalg5uPiGdXHOWbOTEOioIXfReEeAuLviTRXhdTGvZtTnYtDm2eZonv8buTf73YKIzJHV4i00YikF7WiB`

**Step 1: Submit payment with `ACH` type**

```json
{
  "data": {
    "payments": [
      {
        "paymentMethodType": "ACH",
        "amountCents": 750
      }
    ]
  }
}
```

**Response (200 OK — pending, needs Stripe confirmation):**

```json
{
  "data": {
    "id": "transaction-event-uuid",
    "type": "payment",
    "status": "pending",
    "orderId": "order-uuid",
    "settledAt": null
  },
  "included": {
    "payments": [
      {
        "id": "payment-uuid",
        "orderId": "order-uuid",
        "referenceId": "pi_3T5tvECMyY4UUjhB1Is9sEQ2",
        "gateway": "stripe",
        "gatewayData": {
          "provider": "stripe",
          "paymentIntentId": "pi_3T5tvECMyY4UUjhB1Is9sEQ2",
          "clientSecret": "pi_3T5tvECMyY4UUjhB1Is9sEQ2_secret_...",
          "paymentMethods": [
            {
              "id": "pm_1Sygm4CMyY4UUjhBOhNeoApv",
              "card": { "brand": "visa", "exp_month": 1, "exp_year": 2031, "last4": "7510" }
            }
          ]
        },
        "amount": 750,
        "currency": "USD",
        "status": "pending",
        "paymentMethodType": "ACH"
      }
    ]
  }
}
```

**Key fields in `gatewayData`:**
- `paymentIntentId` — the Stripe PaymentIntent ID (`pi_...`)
- `clientSecret` — the client secret needed to confirm the PaymentIntent
- `paymentMethods[]` — the user's saved cards (same data as from `payment-method-setup`)

**Step 2: Confirm the PaymentIntent via Stripe API**

```bash
curl -s -X POST "https://api.stripe.com/v1/payment_intents/${PAYMENT_INTENT_ID}/confirm" \
  -u "${STRIPE_PUBLISHABLE_KEY}:" \
  -d "payment_method=${PAYMENT_METHOD_ID}" \
  -d "client_secret=${CLIENT_SECRET}"
```

**Response:**

```json
{
  "id": "pi_3T5tvECMyY4UUjhB1Is9sEQ2",
  "status": "succeeded",
  "amount": 750,
  "currency": "usd"
}
```

Once Stripe confirms the payment, the rec.us order is automatically settled via webhook. The order's `totalAmountRemaining` drops to 0 and the payment status changes to `succeeded`.

### Current User

```
🔒 GET /v1/users/me                                → current user profile
```

Returns the authenticated user's profile. The `id` field is the rec.us user UUID (not the Firebase UID).

**Response:**

```json
{
  "id": "9101112a-3912-4cda-8814-8cd29586bd0f",
  "householdId": "7a8da9f0-93ce-4578-bfc8-61cc36fbfbf0",
  "firebaseUserId": "1N78WJBXjdU1avTCTx9z1JkFWMv1",
  "recId": "EID223",
  "email": "user@example.com",
  "role": "user",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "2234445555",
  "formattedAddress": "455 Vallejo St., San Francisco, CA 94133, USA",
  "skillLevel": "first-timer",
  "isInstructor": false,
  "memberships": [],
  "organizationRoles": {},
  "profile": {
    "id": "profile-uuid",
    "userId": "9101112a-3912-4cda-8814-8cd29586bd0f",
    "dateOfBirth": null,
    "gender": null,
    "email": "user@example.com",
    "phone": "2234445555"
  }
}
```

**Notes:**
- The `id` (rec.us UUID) is needed for user-scoped endpoints like `/v1/users/{userId}/bookings`. This is **not** the same as `firebaseUserId`.

### User's Bookings

```
🔒 GET /v1/users/{userId}/bookings                 → all bookings
🔒 GET /v1/users/{userId}/planned-bookings          → upcoming bookings (sideloaded includes)
```

Both are **paginated** (`data`/`meta` envelope — see Pagination).

**Response item:**

```json
{
  "id": "75894d52-d00f-4fc3-acdc-6c94832dcf67",
  "status": "confirmed",
  "createdAt": "2026-02-26T18:25:05.718Z",
  "updatedAt": "2026-02-26T18:25:23.032Z",
  "canceledAt": null,
  "cancelReason": null,
  "canceledByUserId": null,
  "creatorUserId": "user-uuid",
  "customerUserId": "user-uuid",
  "participantUserId": "user-uuid",
  "organizationId": "org-uuid",
  "isFastTrack": false,
  "sectionId": null,
  "sessionId": null,
  "linkedReservationId": null,
  "facilityRentalId": "facility-rental-uuid",
  "type": "facilityRental",
  "timeStatus": "future"
}
```

**Notes:**
- `timeStatus` — `"future"` for upcoming bookings, `"past"` for completed ones.
- `canceledAt` — non-null if the booking was cancelled.
- `type` — `"facilityRental"` for site bookings, `"session"` for group classes, etc.
- `planned-bookings` returns only upcoming bookings and supports sideloaded includes (see below), but may return empty if no planned bookings exist.

### Booking Detail

```
🔒 GET /v1/bookings/{bookingId}                    → single booking with includes
```

**Query parameters:**

| Parameter | Description |
|---|---|
| `include[]` | Sideloaded relations (repeatable). Values: `facilityRental`, `section`, `reservations`, `sites`, `locations`, `reservationSiteIds`, `customer`, `participant` |

**Example:**

```
GET /v1/bookings/{bookingId}?include[]=facilityRental&include[]=reservations&include[]=sites&include[]=locations&include[]=reservationSiteIds
```

**Response:**

```json
{
  "data": {
    "booking": {
      "id": "booking-uuid",
      "status": "confirmed",
      "canceledAt": null,
      "organizationId": "org-uuid",
      "facilityRentalId": "facility-rental-uuid",
      "type": "facilityRental"
    }
  },
  "included": {
    "facilityRental": {
      "id": "facility-rental-uuid",
      "name": "Court Reservation: A",
      "status": "confirmed",
      "bookingType": "instant",
      "canceledAt": null
    },
    "reservations": [
      {
        "id": "reservation-uuid",
        "locationId": "location-uuid",
        "reservationCost": 0,
        "reservationCostCurrency": "USD",
        "reservationType": "court-reservation",
        "reservationTimestampRange": ["2026-03-05 13:00:00", "2026-03-05 14:00:00"],
        "startsAt": "2026-03-05T21:00:00.000Z",
        "endsAt": "2026-03-05T22:00:00.000Z",
        "canceledAt": null
      }
    ],
    "sites": [
      {
        "id": "site-uuid",
        "locationId": "location-uuid",
        "courtNumber": "A",
        "type": "court"
      }
    ],
    "locations": [
      {
        "id": "location-uuid",
        "name": "Granada Park",
        "timezone": "America/Los_Angeles"
      }
    ],
    "reservationSiteIds": {
      "reservation-uuid": ["site-uuid"]
    }
  }
}
```

### Cancelling a Booking

```
🔒 GET  /v1/bookings/{bookingId}/refund-eligibility-deadline  → check refund eligibility
🔒 GET  /v1/bookings/{bookingId}/refund-preview               → preview refund amount & destinations
🔒 POST /v1/bookings/{bookingId}/cancel                       → cancel the booking
```

#### Refund eligibility

```
GET /v1/bookings/{bookingId}/refund-eligibility-deadline
```

**Response:**

```json
{
  "data": {
    "suggestionGenerated": true,
    "eligibleUntil": "2026-03-04T10:00:00Z",
    "recommendationJustification": "..."
  }
}
```

The frontend polls this every 1 second until `suggestionGenerated` is `true`. If `eligibleUntil` is in the future, a refund is available.

#### Refund preview

```
GET /v1/bookings/{bookingId}/refund-preview
```

**Response (paid booking):**

```json
{
  "data": {
    "applicable": true,
    "eligibleDestinations": ["original_payment_methods", "account_credit"],
    "destinations": {
      "originalPaymentMethods": {
        "amountCents": 750,
        "formattedAmount": "$7.50",
        "destinationSummary": "Visa ending in 7510"
      },
      "accountCredit": {
        "amountCents": 750,
        "formattedAmount": "$7.50",
        "destinationSummary": "Account credit"
      }
    },
    "refundType": "full"
  }
}
```

**Response (free booking):**

```json
{
  "data": {
    "applicable": false,
    "reason": "unsupported_booking_type"
  }
}
```

**Notes:**
- `refundType` — `"full"`, `"partial"`, or `"zero"`.
- `applicable: false` for free ($0) bookings — no refund preview needed, just cancel directly.

#### Cancel

```
POST /v1/bookings/{bookingId}/cancel
```

**Request body (paid booking — choose refund destination):**

```json
{
  "data": {
    "refundDestination": "original_payment_methods"
  }
}
```

**Request body (free booking — no body needed):**

Empty POST (no body, or empty `{}`).

**Response (200 OK):**

```json
{
  "data": {
    "id": "booking-uuid",
    "status": "confirmed",
    "canceledAt": "2026-03-03T21:36:44.057Z",
    "canceledByUserId": "user-uuid",
    "facilityRentalId": "facility-rental-uuid",
    "type": "facilityRental"
  }
}
```

**Notes:**
- `canceledAt` is set on success. The `status` remains `"confirmed"` (not changed to `"cancelled"`).
- `refundDestination` values: `"original_payment_methods"` or `"account_credit"`.
- For free bookings, the `refund-preview` returns `applicable: false` — skip the refund flow and just POST cancel directly.

### Organizations (admin)

```
GET    /v1/organizations/{slugOrId}/groups         → org membership groups
GET    /v1/organizations/{slugOrId}/stored-value    → stored value accounts
GET    /v1/organizations/{slugOrId}/desk            → front desk view
```

### Payments

```
GET    /v1/payments/{paymentId}                    → payment detail
POST   /v1/payments/{paymentId}/cancel              → cancel payment
```

---

## Example: Find Available Pickleball Sites

```bash
# 1. List organizations
curl -s 'https://api.rec.us/v1/organizations' | jq '.data[].slug'

# 2. Get org detail to find location IDs (in config.banners.pages)
curl -s 'https://api.rec.us/v1/organizations/san-francisco-rec-park' | jq '.config.banners.pages | keys[]'

# 3. Get location detail
curl -s 'https://api.rec.us/v1/locations/ad9e28e1-2d02-4fb5-b31d-b75f63841814' | jq '.location.name, .location.courts[].courtNumber'

# 4. Check schedule for available slots
curl -s 'https://api.rec.us/v1/locations/ad9e28e1-2d02-4fb5-b31d-b75f63841814/schedule?startDate=2026-03-01' | \
  jq '.dates["20260301"][] | select(.sports[].name == "Pickleball") | {court: .courtNumber, slots: [.schedule | to_entries[] | select(.value.referenceType == "RESERVABLE") | .key]}'
```

## Example: Find Available Tennis Instructors

```bash
# 1. List instructors with open lesson slots
curl -s 'https://api.rec.us/v1/instructors/cards/lessons?organizationSlug=san-francisco-rec-park' | \
  jq '.[] | {name: .fullName, sport: .sports[0].name, rate: .sports[0].hourlyRate, nextLesson: .lessons[0].reservationTimestampRange}'

# 2. Get full instructor profile
curl -s 'https://api.rec.us/v1/instructors/{instructorId}' | jq '{name: .user.firstName + " " + .user.lastName, bio: .longBio, locations: [.instructorLocations[].locationId]}'
```

## Example: Find Group Classes

```bash
# List all programs for SF Rec Park in the next 90 days
curl -s 'https://api.rec.us/v1/discovery/programmed?organizationId=17380e28-7e02-4b52-82c5-fab18557fd7a&startDate=2026-02-27&endDate=2026-05-27' | \
  jq '.[] | {name: .name, sport: .sportName, location: .locationName, spots: (.capacity - .participantCount), sessions: (.sessions | length)}'
```

## Example: Book a Free Site (Full Flow)

End-to-end example booking a free pickleball site at Granada Park.

```bash
# 1. Authenticate
TOKEN=$(curl -s -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCp6DCwnx-6GwkMyI2G1b8ixYs4AXZc-7s' \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"password","returnSecureToken":true}' \
  | jq -r '.idToken')

# 2. Find the location — search by region or org
#    Granada Park is in the San Francisco Area region
curl -s 'https://api.rec.us/v1/locations/availability?regionId=51cad8df-4985-4c09-ba5e-c7893f672c26' | \
  jq '.[] | select(.location.name == "Granada Park") | .location | {id, name, courts: [.courts[] | {id, court: .courtNumber, pricing: .config.pricing.default}]}'

# 3. Check the schedule for available pickleball slots on a specific date
LOCATION_ID="38a201f0-4fb1-4991-8e72-db8a9495319e"
curl -s "https://api.rec.us/v1/locations/$LOCATION_ID/schedule?startDate=2026-03-05" | \
  jq '.dates["20260305"][] | select(.sports[].name == "Pickleball") | {court: .courtNumber, slots: [.schedule | to_entries[] | select(.value.referenceType == "RESERVABLE") | .key]}'

# 4. Verify the site supports instant booking
SITE_ID="99b7129e-5ed4-4fd8-aba2-fee1683310bb"   # Site A (court)
curl -s "https://api.rec.us/v1/sites/$SITE_ID" \
  -H "Authorization: Bearer $TOKEN" | \
  jq '.data | {id, courtNumber, isInstantBookable, capacity}'

# 5. Create the reservation
ORDER_ID=$(curl -s -X POST 'https://api.rec.us/v1/facility-rentals' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"data\": {
      \"reservation\": {
        \"timestampRange\": \"[2026-03-05 13:00:00, 2026-03-05 14:00:00)\",
        \"locationId\": \"$LOCATION_ID\",
        \"courtIds\": [\"$SITE_ID\"]
      }
    }
  }" | jq -r '.data.order.id')

echo "Order created: $ORDER_ID"

# 6. Complete the order (required even for $0 reservations)
curl -s -X POST "https://api.rec.us/v1/orders/$ORDER_ID/pay" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data":{"payments":[{"paymentMethodType":"free","amountCents":0}]}}' | \
  jq '.data | {status, settledAt}'

# 7. Verify — the slot should now show as RESERVATION
curl -s "https://api.rec.us/v1/locations/$LOCATION_ID/schedule?startDate=2026-03-05" | \
  jq '.dates["20260305"][] | select(.courtNumber == "A") | .schedule["13:00, 14:00"]'
# → { "referenceType": "RESERVATION", "referenceId": "..." }
```

**Key points:**
- After `POST /v1/facility-rentals`, the order is `"pending"` with a ~10 minute expiration. You **must** call `POST /v1/orders/{orderId}/pay` to finalize it.
- For free sites, use `paymentMethodType: "free"` with `amountCents: 0`.
- The `timestampRange` uses PostgreSQL range syntax: `[start, end)` — inclusive start, exclusive end.
- Times in `timestampRange` are in the location's local timezone (e.g. `America/Los_Angeles`).

## Example: Book a Paid Site (Full Flow)

Same as the free site flow above, but diverges at step 4 — the site has a `fixed-slots` booking policy, and payment requires a Stripe confirmation step.

```bash
# Steps 1-3 are the same as "Book a Free Site" (authenticate, find location, check schedule).

# 4. Get site detail — check booking policy and pricing
SITE_ID="040a5a1a-443a-4641-b079-ed7e650bd5ac"   # J.P. Murphy site "Court 3"
curl -s "https://api.rec.us/v1/sites/$SITE_ID" \
  -H "Authorization: Bearer $TOKEN" | \
  jq '.data | {id, courtNumber, isInstantBookable, noReservationText,
    pricing: .config.pricing.default,
    bookingPolicy: .config.bookingPolicies[0].type,
    fixedSlots: [.config.bookingPolicies[0].slots[] | select(.dayOfWeek == 7) | {start: .startTimeLocal, end: .endTimeLocal}]}'
# → bookingPolicy: "fixed-slots", fixedSlots: [{start: "16:30:00", end: "18:00:00"}, ...]
# With fixed-slots, your timestampRange MUST match a slot exactly.

# 5. Create the reservation (timestampRange matches the fixed slot 16:30-18:00)
LOCATION_ID="7a8ef25a-dc20-4046-8aab-7212a9a41d20"
RESULT=$(curl -s -X POST 'https://api.rec.us/v1/facility-rentals' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"data\": {
      \"reservation\": {
        \"timestampRange\": \"[2026-03-01 16:30:00, 2026-03-01 18:00:00)\",
        \"locationId\": \"$LOCATION_ID\",
        \"courtIds\": [\"$SITE_ID\"]
      }
    }
  }")
ORDER_ID=$(echo "$RESULT" | jq -r '.data.order.id')
ITEM_ID=$(echo "$RESULT" | jq -r '.data.order.items[0].id')
TOTAL=$(echo "$RESULT" | jq -r '.data.order.total')
echo "Order: $ORDER_ID, Item: $ITEM_ID, Total: $TOTAL cents"
# → Total: 750 (= $7.50 for 1.5 hours at $5/hour)

# 6. Look up saved payment methods
USER_ID=$(echo "$RESULT" | jq -r '.data.order.customer.id')
ORG_ID=$(echo "$RESULT" | jq -r '.data.order.organization.id')
curl -s -X POST "https://api.rec.us/v1/users/$USER_ID/payment-method-setup" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"data\":{\"organizationId\":\"$ORG_ID\"}}" | \
  jq '.data.paymentMethods[] | {id, brand: .card.brand, last4: .card.last4}'
# → { "id": "pm_1Sygm4CMyY4UUjhBOhNeoApv", "brand": "visa", "last4": "7510" }

# 7. Submit payment (use "ACH" type — "cardOnline" is rejected by the API)
PAY_RESULT=$(curl -s -X POST "https://api.rec.us/v1/orders/$ORDER_ID/pay" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"data\":{\"payments\":[{\"paymentMethodType\":\"ACH\",\"amountCents\":$TOTAL}]}}")

# Extract Stripe PaymentIntent details from the response
PI_ID=$(echo "$PAY_RESULT" | jq -r '.included.payments[0].gatewayData.paymentIntentId')
CLIENT_SECRET=$(echo "$PAY_RESULT" | jq -r '.included.payments[0].gatewayData.clientSecret')
echo "PaymentIntent: $PI_ID"

# 8. Confirm the PaymentIntent with Stripe using the saved card
PM_ID="pm_1Sygm4CMyY4UUjhBOhNeoApv"  # from step 6
STRIPE_PK="pk_live_51MPUx4CMyY4UUjhBlgalg5uPiGdXHOWbOTEOioIXfReEeAuLviTRXhdTGvZtTnYtDm2eZonv8buTf73YKIzJHV4i00YikF7WiB"
curl -s -X POST "https://api.stripe.com/v1/payment_intents/$PI_ID/confirm" \
  -u "$STRIPE_PK:" \
  -d "payment_method=$PM_ID" \
  -d "client_secret=$CLIENT_SECRET" | \
  jq '{status, amount, currency}'
# → { "status": "succeeded", "amount": 750, "currency": "usd" }

# 9. Verify — order should show totalAmountRemaining: 0
curl -s "https://api.rec.us/v1/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN" | \
  jq '.order | {status, total, totalAmountRemaining}'
```

**Key differences from the free site flow:**
- **Fixed-slots sites** require `timestampRange` to exactly match a pre-defined slot boundary (check `config.bookingPolicies`). Using a custom duration like `[16:30, 17:30)` will fail with `"The reservation violates the site's booking policy"`.
- **Card payment** is a two-step process: (1) call `/pay` with `paymentMethodType: "ACH"` to create a Stripe PaymentIntent, then (2) confirm it via the Stripe API with a saved `payment_method` ID.
- The Stripe publishable key authenticates the `/confirm` call (passed as HTTP basic auth username with empty password).
- After Stripe confirmation, rec.us is notified via webhook and the order settles automatically.
- **Daily booking limits** exist per location/date (e.g. 1 reservation per day). Expired unpaid orders may still count against the limit temporarily. The error is `E_INELIGIBLE_SITE_BOOKING` with a message like `"Daily booking limit of 1 reached for March 1, 2026"`.
