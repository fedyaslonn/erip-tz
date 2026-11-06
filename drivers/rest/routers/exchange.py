from typing import Annotated

from fastapi import APIRouter, Depends, Query

from domain.schemas.exchange import (
    ExchangeConfirmResponse,
    ExchangeConfirmRequest,
    ExchangeQuoteResponse,
    ExchangeQuoteRequest,
    PendingDealResponse,
)
from domain.schemas.stats import CurrencyAggregatedStats, DealStatsFilter
from services.protocols import IExchangeService
from services.exchange import ExchangeService
from persistence.uow import SQLAlchemyUnitOfWork
from persistence.db import async_session_maker

router = APIRouter(prefix="/api/exchange", tags=["Exchange"])


def get_exchange_service() -> IExchangeService:
    return ExchangeService(lambda: SQLAlchemyUnitOfWork(async_session_maker))


@router.post(
    "/quote",
    response_model=ExchangeQuoteResponse,
    status_code=201,
    responses={
        404: {"description": "Currency not found in rates"},
        503: {"description": "No saved rates"},
        422: {"description": "Invalid currencies or amount"},
    },
)
async def get_quote(
    request: ExchangeQuoteRequest,
    service: Annotated[IExchangeService, Depends(get_exchange_service)],
) -> ExchangeQuoteResponse:
    return await service.get_quote(request)


@router.post(
    "/confirm",
    response_model=ExchangeConfirmResponse,
    responses={
        404: {"description": "Deal not found"},
        409: {"description": "Deal already processed"},
    },
)
async def confirm_deal(
    request: ExchangeConfirmRequest,
    service: Annotated[IExchangeService, Depends(get_exchange_service)],
) -> ExchangeConfirmResponse:
    return await service.confirm_deal(request)


@router.get(
    "/pending",
    response_model=list[PendingDealResponse],
)
async def get_pending_deals(
    service: Annotated[IExchangeService, Depends(get_exchange_service)],
) -> list[PendingDealResponse]:
    return await service.get_pending_deals()


@router.get(
    "/stats",
    response_model=list[CurrencyAggregatedStats],
)
async def get_stats(
    filters: Annotated[DealStatsFilter, Query()],
    service: Annotated[IExchangeService, Depends(get_exchange_service)],
) -> list[CurrencyAggregatedStats]:
    return await service.get_stats(filters)
