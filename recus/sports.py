from __future__ import annotations

_EMOJI: dict[str, str] = {
    "5d391ce4-ef26-44b8-b75b-d2aff5441e37": "🏸",  # Badminton
    "0245e844-025e-4608-b0bf-8481a3de04d1": "⚾",  # Baseball
    "8a17a248-dbb3-4869-a170-1c92a3fdb826": "🏀",  # Basketball
    "3a0daefe-9130-46f3-85cd-d97c77a0dae6": "🟢",  # Bocce Ball
    "83b6699d-df77-427d-bcb4-f1e51a4200dd": "🏈",  # Football
    "7db2bbbd-f138-4feb-aeb1-fa111024238e": "⚽",  # Futsal
    "950ddbad-2a13-49f8-9436-3c2a7e084830": "⛳",  # Golf
    "a7b0e429-3e32-4c3c-9775-6ef4ea3fb985": "🏟",  # Multi-Sport Court
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": "🏓",  # Pickleball
    "ec3f6b6e-80ff-4c7a-903c-3a72f8c3d877": "🏸",  # Racquetball
    "ba04e296-e7fe-454b-9d8f-d0e162965883": "🏒",  # Roller Hockey
    "fc0ac7d7-f404-49f4-a2b3-e83b9ce9df3f": "⚽",  # Soccer
    "ae44d41a-8a56-46af-97db-4c19c93b0400": "🥎",  # Softball
    "e766548e-978a-4f2f-a6fb-7f578a3a6b1d": "🏊",  # Swimming
    "bd745b6e-1dd6-43e2-a69f-06f094808a96": "🎾",  # Tennis
    "9e8275d2-dd11-4ec8-9eea-3c71b57d483f": "🏐",  # Volleyball
}

_DEFAULT = "🏟"


def sport_emojis(sport_ids: list[str]) -> str:
    """Return emojis for all recognized sports, deduped, or the default."""
    seen: dict[str, None] = {}
    for sid in sport_ids:
        e = _EMOJI.get(sid)
        if e and e not in seen:
            seen[e] = None
    return "".join(seen) if seen else _DEFAULT
