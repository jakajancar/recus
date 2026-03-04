from __future__ import annotations

from pydantic import BaseModel


class PostFacilityRentalResponse(BaseModel):
    data: RentalData


class RentalData(BaseModel):
    order: Order


class Order(BaseModel):
    id: str
    total: int
    customer: OrderCustomer | None = None
    organization: OrderOrganization | None = None
    items: list[OrderItem] = []


class OrderCustomer(BaseModel):
    id: str


class OrderOrganization(BaseModel):
    id: str


class OrderItem(BaseModel):
    id: str
    details: OrderItemDetails


class OrderItemDetails(BaseModel):
    bookingId: str
