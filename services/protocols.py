from typing import Protocol

from domain.schemas.exchange import (
    ExchangeConfirmResponse,
    ExchangeConfirmRequest,
    ExchangeQuoteResponse,
    ExchangeQuoteRequest,
    PendingDealResponse,
)
from domain.schemas.stats import CurrencyAggregatedStats, DealStatsFilter


class IExchangeService(Protocol):
    async def get_quote(
        self, request: ExchangeQuoteRequest
    ) -> ExchangeQuoteResponse: ...

    async def confirm_deal(
        self, request: ExchangeConfirmRequest
    ) -> ExchangeConfirmResponse: ...

    async def get_pending_deals(self) -> list[PendingDealResponse]: ...

    async def get_stats(
        self, filters: DealStatsFilter
    ) -> list[CurrencyAggregatedStats]: ...
