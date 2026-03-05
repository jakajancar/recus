# recus

A CLI for [rec.us](https://rec.us), a booking platform for parks & recreation.

Because you (or your Claw 🦞) shouldn't need to fuss with the web browser to can snag a court.

See also: [the reverse-engineered API documentation](https://jakajancar.github.io/recus/api.html)


## Installation

```
uv tool install git+https://github.com/jakajancar/recus
```

## Usage

### Log in

```
recus login
```

Prompts for your rec.us email and password. Tokens are stored in `~/.recus/state.json` and refresh automatically.

Multiple accounts are supported -- use `--account <email>` to select one.

### Browse organizations and regions

```
recus orgs
recus regions
```

Find the org slug or region UUID you want to search.

### Search available courts

```
$ recus avails --org san-francisco-rec-park
📍 Alice Marble · 1200 Greenwich St, San Francisco, CA 94109, USA · 7:30am to
7:30pm (81cd2b08-8ea6-40ee-8c89-aeba92506576)
    🎾 Court 2 · Tennis · $5/hr (438ee54a-072c-43b4-a990-f78f9eba47b2)
        Wed Mar  4: 07:30 (90min), 10:30 (90min), 12:00 (90min), 13:30 (90min)
        Thu Mar  5: 07:30 (90min), 10:30 (90min), 12:00 (90min), 13:30 (90min)
        Fri Mar  6: 13:30 (90min)
        Sun Mar  8: 07:30 (90min), 12:00 (90min), 18:00 (90min)
        Mon Mar  9: 07:30 (90min), 09:00 (90min), 10:30 (90min), 12:00 (90min),
13:30 (90min)
        Tue Mar 10: 07:30 (90min), 09:00 (90min), 10:30 (90min), 12:00 (90min),
13:30 (90min)
        Opens 7d ahead at 8:00 am
    🎾 Court 4 · Tennis · $5/hr (c95ae7df-6b71-4ac6-93fc-d72e6e73be37)
        Wed Mar  4: 07:00 (60min), 11:00 (60min), 12:00 (60min)
        Thu Mar  5: 08:00 (60min), 09:00 (60min), 11:00 (60min), 12:00 (60min),
13:00 (60min), 14:00 (60min), 15:00 (60min)
        Opens 2d ahead at 12:00 pm
    🎾 Court 1 · Tennis · $5/hr (f16d5170-6698-4275-90c1-f0e5e499eb52)
        ...
    🎾 Court 3 · Tennis · $5/hr (c520577d-2c22-4e4e-8a92-c7709b0df07b)
        ...

📍 Balboa · Ocean Ave & San Jose Avenue, San Francisco, CA 94112, USA
📍 Buena Vista · 198 Buena Vista Ave E, San Francisco, CA 94117, USA
📍 Crocker Amazon · 799 Moscow St, San Francisco, CA 94112, USA
📍 Dolores · 3753 18th St, San Francisco, CA 94114, USA
📍 DuPont · 336 31st Ave, San Francisco, CA 94121, USA
📍 Fulton · 855 27th Ave, San Francisco, CA 94121, USA
📍 Glen Canyon · 70 Elk St, San Francisco, CA 94131, USA
📍 Hamilton · 1900 Geary Blvd, San Francisco, CA 94115, USA
📍 Helen Wills · 1401 Broadway, San Francisco, CA 94109, USA
📍 Jackson · 1500 Mariposa St, San Francisco, CA 94107, USA
📍 Joe DiMaggio · 651 Lombard St, San Francisco, CA 94133, USA
📍 J.P. Murphy · 1960 9th Ave, San Francisco, CA 94116, USA
📍 Lafayette · Gough St & Washington St, San Francisco, CA 94109, USA
📍 McLaren · 1398 Mansell St #1200, San Francisco, CA 94134, USA
📍 Minnie & Lovie Ward · 650 Capitol Ave, San Francisco, CA 94112, USA
📍 Miraloma · 75 Sequoia Way, San Francisco, CA 94127, USA
📍 Moscone · 1800 Chestnut St, San Francisco, CA 94123, USA
📍 Mountain Lake · 1 12th Ave, San Francisco, CA 94118, USA
📍 Parkside Square · 2680 28th Ave, San Francisco, CA 94116, USA
📍 Potrero Hill · 801 Arkansas St, San Francisco, CA 94107, USA
📍 Presidio Wall · Spruce St & Pacific Ave, San Francisco, CA 94118, USA
📍 Richmond · 18th Ave & Lake St, San Francisco, CA 94121, USA
📍 Rossi · 600 Arguello Blvd, San Francisco, CA 94118, USA
📍 Stern Grove · 19th Ave & Sloat Blvd, San Francisco, CA 94132, USA
📍 St. Mary's · 95 Justin Dr, San Francisco, CA 94112, USA
📍 Sunset · 2201 Lawton St, San Francisco, CA 94122, USA
📍 Upper Noe · 295 Day St, San Francisco, CA 94131, USA
... (each with full court/slot details)
```

Or search by region UUID with `--region` instead of `--org`.

Each court line includes the site UUID needed for booking.

### Create a booking

```
recus booking create <site-uuid> "2026-03-15 10:00" 90
```

- `site-uuid`: from the `avails` output
- Start time in `YYYY-MM-DD HH:MM` format (location timezone)
- Duration in minutes (e.g. 60, 90)

Paid bookings use your most recently added card on file.

### List bookings

```
recus booking list
```

### Cancel a booking

```
recus booking cancel <booking-id>
```

Attempts refund to the original payment method, then account credit.

### Low-level API access

```
recus get /v1/organizations
recus get --auth /v1/users/me
```

GET any API path and pretty-print the JSON response. Use `--auth` to include your authentication token.

### Log out

```
recus logout
```
