import uuid
import enum
from datetime import datetime
from decimal import Decimal

from pydantic import model_validator, field_validator, ConfigDict, BaseModel, Field

from persistence.models import TransactionStatus


class DealAction(str, enum.Enum):
    CONFIRM = "COMPLETED"
    REJECT = "REJECTED"


class ExchangeQuoteRequest(BaseModel):
    source_amount: Decimal = Field(..., gt=0, max_digits=14, decimal_places=2)
    source_currency: str = Field(..., min_length=3, max_length=3)
    target_currency: str = Field(..., min_length=3, max_length=3)

    @field_validator("source_currency", "target_currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def check_different_currencies(self) -> "ExchangeQuoteRequest":
        if self.source_currency == self.target_currency:
            raise ValueError("Source and target currencies must be different")
        return self


class ExchangeQuoteResponse(BaseModel):
    deal_id: uuid.UUID
    target_amount: Decimal
    exchange_rate: Decimal


class ExchangeConfirmRequest(BaseModel):
    deal_id: uuid.UUID
    result: DealAction

    @field_validator("result", mode="before")
    @classmethod
    def normalize_result(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value


class ExchangeConfirmResponse(BaseModel):
    deal_id: uuid.UUID
    status: TransactionStatus
    updated_at: datetime


class PendingDealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_amount: Decimal
    target_amount: Decimal
    source_currency: str
    target_currency: str
    exchange_rate: Decimal
