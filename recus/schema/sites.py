from __future__ import annotations

from pydantic import BaseModel


class GetSiteDetailResponse(BaseModel):
    data: SiteDetail


class SiteDetail(BaseModel):
    id: str
    locationId: str
    noReservationText: str | None
    isInstantBookable: bool
