from __future__ import annotations

from pydantic import BaseModel, RootModel


class Sport(BaseModel):
    id: str
    name: str


# RootModel must follow its type parameter (class bases are evaluated eagerly).
class GetSportsResponse(RootModel[list[Sport]]):
    pass
