import uuid
from datetime import date
from typing import Protocol

from domain.schemas.stats import CurrencyAggregatedStats
from persistence.models import ExchangeTransaction, ExchangeRate


class IRateRepository(Protocol):
    async def get_by_date(
        self, rate_date: date, currency_code: str
    ) -> ExchangeRate | None: ...

    async def get_all_by_date(self, rate_date: date) -> list[ExchangeRate]: ...

    async def get_latest_date(self, today: date) -> date | None: ...

    async def save_daily(self, rates: list[dict]) -> None: ...

    def add(self, rate: ExchangeRate) -> None: ...

    def add_all(self, rates: list[ExchangeRate]) -> None: ...


class ITransactionRepository(Protocol):
    async def get_by_id(
        self, deal_id: uuid.UUID, for_update: bool = False
    ) -> ExchangeTransaction | None: ...

    async def get_pending_deals(self) -> list[ExchangeTransaction]: ...

    async def get_stats(
        self, date_from: date, date_to: date, currency: str | None = None
    ) -> list[CurrencyAggregatedStats]: ...

    def add(self, transaction: ExchangeTransaction) -> None: ...
