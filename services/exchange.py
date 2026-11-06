import uuid
from zoneinfo import ZoneInfo
from datetime import timezone, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable

from exceptions.business_exceptions import (
    CurrencyNotFoundError,
    DealNotFoundError,
    ExternalAPIError,
)
from domain.schemas.exchange import (
    ExchangeConfirmResponse,
    ExchangeConfirmRequest,
    ExchangeQuoteResponse,
    ExchangeQuoteRequest,
    PendingDealResponse,
)
from services.state_machine import TransactionStateMachine
from domain.schemas.stats import CurrencyAggregatedStats, DealStatsFilter
from persistence.models import ExchangeTransaction, TransactionStatus, ExchangeRate
from persistence.uow import IUnitOfWork


class ExchangeService:
    RATE_PRECISION = Decimal("0.000000000001")
    AMOUNT_PRECISION = Decimal("0.01")

    def __init__(self, uow_factory: Callable[[], IUnitOfWork]):
        self.uow_factory = uow_factory

    async def get_quote(self, request: ExchangeQuoteRequest) -> ExchangeQuoteResponse:
        today = datetime.now(ZoneInfo("Europe/Minsk")).date()
        async with self.uow_factory() as uow:
            rate_date = await uow.rates.get_latest_date(today)
            if rate_date is None:
                raise ExternalAPIError("No exchange rates available")
            rates = {
                rate.currency_code: rate
                for rate in await uow.rates.get_all_by_date(rate_date)
            }
            source_rate = self.get_unit_rate(request.source_currency, rates)
            target_rate = self.get_unit_rate(request.target_currency, rates)
            exchange_rate = (source_rate / target_rate).quantize(
                self.RATE_PRECISION, ROUND_HALF_UP
            )
            target_amount = (request.source_amount * exchange_rate).quantize(
                self.AMOUNT_PRECISION, ROUND_HALF_UP
            )

            transaction = ExchangeTransaction(
                id=uuid.uuid4(),
                source_currency=request.source_currency,
                target_currency=request.target_currency,
                source_amount=request.source_amount,
                target_amount=target_amount,
                exchange_rate=exchange_rate,
                status=TransactionStatus.PENDING,
            )
            uow.transactions.add(transaction)
            response = ExchangeQuoteResponse(
                deal_id=transaction.id,
                target_amount=target_amount,
                exchange_rate=exchange_rate,
            )
        return response

    @staticmethod
    def get_unit_rate(currency: str, rates: dict[str, ExchangeRate]) -> Decimal:
        if currency == "BYN":
            return Decimal(1)
        rate = rates.get(currency)
        if rate is None:
            raise CurrencyNotFoundError(currency)
        return rate.rate / rate.scale

    async def confirm_deal(
        self, request: ExchangeConfirmRequest
    ) -> ExchangeConfirmResponse:
        async with self.uow_factory() as uow:
            transaction = await uow.transactions.get_by_id(
                request.deal_id, for_update=True
            )
            if transaction is None:
                raise DealNotFoundError(str(request.deal_id))
            status = TransactionStatus(request.result.value)
            TransactionStateMachine.validate_transition(
                str(transaction.id), transaction.status, status
            )
            transaction.status = status
            transaction.updated_at = datetime.now(timezone.utc)
            response = ExchangeConfirmResponse(
                deal_id=transaction.id, status=status, updated_at=transaction.updated_at
            )
        return response

    async def get_pending_deals(self) -> list[PendingDealResponse]:
        async with self.uow_factory() as uow:
            transactions = await uow.transactions.get_pending_deals()
            return [
                PendingDealResponse.model_validate(transaction)
                for transaction in transactions
            ]

    async def get_stats(
        self, filters: DealStatsFilter
    ) -> list[CurrencyAggregatedStats]:
        async with self.uow_factory() as uow:
            return await uow.transactions.get_stats(
                filters.date_from, filters.date_to, filters.currency
            )
