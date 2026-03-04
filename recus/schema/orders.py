from __future__ import annotations

from pydantic import BaseModel


class PostPayFreeResponse(BaseModel):
    data: PayStatus


class PostPayACHResponse(BaseModel):
    data: PayStatus
    included: PayACHIncluded


class PayStatus(BaseModel):
    status: str


class PayACHIncluded(BaseModel):
    payments: list[Payment]


class Payment(BaseModel):
    gatewayData: GatewayData


class GatewayData(BaseModel):
    paymentIntentId: str
    clientSecret: str
    paymentMethods: list[PaymentMethod]


class PaymentMethod(BaseModel):
    id: str
    card: Card


class Card(BaseModel):
    brand: str
    last4: str
    exp_month: int
    exp_year: int
