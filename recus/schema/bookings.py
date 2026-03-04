from __future__ import annotations

from pydantic import BaseModel


class Booking(BaseModel):
    id: str
    timeStatus: str | None = None
    canceledAt: str | None = None


class GetBookingDetailResponse(BaseModel):
    data: BookingDetailData
    included: BookingDetailIncluded


class BookingDetailData(BaseModel):
    booking: Booking


class BookingDetailIncluded(BaseModel):
    reservations: list[BookingReservation] = []
    sites: list[BookingSite] = []
    locations: list[BookingLocation] = []


class BookingReservation(BaseModel):
    reservationTimestampRange: list[str] = []


class BookingSite(BaseModel):
    courtNumber: str | None = None


class BookingLocation(BaseModel):
    name: str


class GetRefundEligibilityResponse(BaseModel):
    data: RefundEligibilityData


class RefundEligibilityData(BaseModel):
    suggestionGenerated: bool
    eligibleUntil: str | None = None
    recommendationJustification: str | None = None


class GetRefundPreviewResponse(BaseModel):
    data: RefundPreviewData


class RefundPreviewData(BaseModel):
    applicable: bool
    reason: str | None = None
    eligibleDestinations: list[str] = []
    destinations: RefundDestinations | None = None


class RefundDestinations(BaseModel):
    originalPaymentMethods: RefundDestination | None = None
    accountCredit: RefundDestination | None = None


class RefundDestination(BaseModel):
    formattedAmount: str
    destinationSummary: str
