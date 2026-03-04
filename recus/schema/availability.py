from __future__ import annotations

from pydantic import BaseModel, RootModel


class AvailabilityEntry(BaseModel):
    location: Location


class Location(BaseModel):
    id: str
    name: str
    formattedAddress: str | None
    hoursOfOperation: str | None
    defaultReservationWindow: int | None
    reservationReleaseTimeLocal: str | None
    courts: list[Site]


class Site(BaseModel):
    id: str
    courtNumber: str
    sports: list[SportRef]
    config: SiteConfig
    allowedReservationDurations: AllowedDurations
    availableSlots: list[str]
    isInstantBookable: bool | None  # API sends null for some sites
    defaultReservationWindowDays: int | None
    reservationReleaseTimeLocal: str | None


class SiteConfig(BaseModel):
    pricing: PricingConfig
    bookingPolicies: list[BookingPolicy] | None = None  # key absent from some sites


class PricingConfig(BaseModel):
    default: Pricing | None


class Pricing(BaseModel):
    type: str
    cents: int


class BookingPolicy(BaseModel):
    type: str
    isActive: bool
    slots: list[BookingSlot]


class BookingSlot(BaseModel):
    dayOfWeek: int
    startTimeLocal: str
    endTimeLocal: str


class AllowedDurations(BaseModel):
    minutes: list[int]


class SportRef(BaseModel):
    sportId: str | None


# RootModel must follow its type parameter (class bases are evaluated eagerly).
class GetAvailabilityResponse(RootModel[list[AvailabilityEntry]]):
    pass
