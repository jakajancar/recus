from __future__ import annotations

from pydantic import BaseModel


class ConfirmPaymentIntentResponse(BaseModel):
    status: str
