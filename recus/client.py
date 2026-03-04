from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from recus.output import console, pretty
from recus.state import AuthToken, user_state

_API_URL = "https://api.rec.us"
_FIREBASE_API_KEY = "AIzaSyCp6DCwnx-6GwkMyI2G1b8ixYs4AXZc-7s"
_FIREBASE_SIGNIN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)
_FIREBASE_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"


def _raise_nice(exc: httpx.HTTPStatusError) -> None:
    """Re-raise an HTTP error with the response body included."""

    console.print(f"[bold red]{exc.response.status_code} {exc.response.reason_phrase}[/]")
    try:
        pretty(exc.response.json())
    except Exception:
        console.print(exc.response.text)
    raise SystemExit(1) from exc


class Client:
    def __init__(self) -> None:
        if type(self) is Client:
            raise TypeError("Cannot instantiate Client directly; use a subclass.")

    def _extra_headers(self) -> dict[str, str]:
        return {}

    def get(self, path: str, params: dict | None = None) -> Any:
        resp = httpx.get(
            f"{_API_URL}{path}", params=params,
            headers=self._extra_headers(), timeout=30,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _raise_nice(exc)
        return resp.json()

    def get_all(self, path: str, params: dict | None = None) -> list[dict]:
        """GET all pages, handling both ``data/meta`` and ``results/total`` envelopes."""
        params = dict(params) if params else {}
        all_items: list[dict] = []
        page = 1
        while True:
            params["pg[num]"] = str(page)
            resp = self.get(path, params)
            # data/meta envelope (organizations, bookings)
            if "data" in resp:
                all_items.extend(resp["data"])
                meta = resp.get("meta", {}).get("pg", {})
                if page * meta.get("size", len(resp["data"])) >= meta.get("totalResults", 0):
                    break
            # results/total envelope (sites)
            else:
                all_items.extend(resp["results"])
                page_size = len(resp["results"])
                if not page_size or (page - 1) * page_size + page_size >= resp.get("total", 0):
                    break
            page += 1
        return all_items

    def post(self, path: str, json: dict | None = None) -> Any:
        resp = httpx.post(
            f"{_API_URL}{path}", json=json,
            headers=self._extra_headers(), timeout=30,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _raise_nice(exc)
        return resp.json()


class AnonClient(Client):
    pass


class AuthClient(Client):
    def __init__(self, account: str, /) -> None:
        self.account = account

    def _extra_headers(self) -> dict[str, str]:
        token = self._ensure_fresh()
        return {"Authorization": f"Bearer {token.id_token}"}

    def login(self, password: str) -> None:
        """Authenticate and store credentials."""
        resp = httpx.post(
            _FIREBASE_SIGNIN_URL,
            params={"key": _FIREBASE_API_KEY},
            json={"email": self.account, "password": password, "returnSecureToken": True},
        )
        if resp.status_code != 200:
            detail = resp.json().get("error", {}).get("message", resp.text)
            raise SystemExit(f"Login failed: {detail}")
        data = resp.json()
        token = AuthToken(
            email=data["email"],
            local_id=data["localId"],
            id_token=data["idToken"],
            refresh_token=data["refreshToken"],
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=int(data["expiresIn"])),
        )
        with user_state() as state:
            state.accounts[token.email] = token

    def _ensure_fresh(self) -> AuthToken:
        with user_state() as state:
            token = state.accounts[self.account]
            if token.expired:
                resp = httpx.post(
                    _FIREBASE_REFRESH_URL,
                    params={"key": _FIREBASE_API_KEY},
                    json={"grant_type": "refresh_token", "refresh_token": token.refresh_token},
                )
                if resp.status_code != 200:
                    raise SystemExit(f"Token refresh failed. Run: recus login {self.account}")
                data = resp.json()
                token = AuthToken(
                    email=self.account,
                    local_id=data["user_id"],
                    id_token=data["id_token"],
                    refresh_token=data["refresh_token"],
                    expires_at=datetime.now(timezone.utc) + timedelta(seconds=int(data["expires_in"])),
                )
                state.accounts[self.account] = token
        return token
