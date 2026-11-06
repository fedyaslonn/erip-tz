from datetime import date
from decimal import Decimal

from pydantic import model_validator, field_validator, BaseModel, Field


class DealStatsFilter(BaseModel):
    date_from: date
    date_to: date
    currency: str | None = Field(None)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str | None) -> str | None:
        return v.upper() if v else None

    @model_validator(mode="after")
    def check_dates(self) -> "DealStatsFilter":
        if self.date_to == date.max:
            raise ValueError("date_to must be earlier than 9999-12-31")
        if self.date_from > self.date_to:
            raise ValueError("date_from cannot be greater than date_to")
        return self


class CurrencyAggregatedStats(BaseModel):
    currency: str
    total_received: Decimal
    total_spent: Decimal
    deals_count: int
