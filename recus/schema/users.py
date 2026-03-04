from __future__ import annotations

from pydantic import BaseModel


class GetMeResponse(BaseModel):
    id: str
