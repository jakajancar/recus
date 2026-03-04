from __future__ import annotations

import fcntl
import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

_USER_STATE_PATH = Path.home() / ".recus" / "state.json"

class UserState(BaseModel):
    accounts: dict[str, AuthToken] = {}


class AuthToken(BaseModel):
    email: str
    local_id: str
    id_token: str
    refresh_token: str
    expires_at: datetime

    @property
    def expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


@contextmanager
def user_state() -> Generator[UserState, None, None]:
    """Lock, read, yield, save, unlock the user's ~/.recus/state.json."""
    _USER_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(_USER_STATE_PATH, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        with os.fdopen(fd, "r+", closefd=False) as f:
            content = f.read()
            state = UserState.model_validate_json(content) if content else UserState()
            yield state
            f.seek(0)
            f.write(state.model_dump_json(indent=2))
            f.truncate()
    finally:
        os.close(fd)
