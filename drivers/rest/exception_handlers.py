import logging

from fastapi.responses import JSONResponse
from fastapi import Request, FastAPI

from exceptions.validation_exceptions import (
    DealAlreadyProcessedError,
    InvalidCurrencyPairError,
    InvalidAmountError,
)
from exceptions.business_exceptions import (
    CurrencyNotFoundError,
    DealNotFoundError,
    ExternalAPIError,
)

logger = logging.getLogger(__name__)


async def currency_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, CurrencyNotFoundError):
        raise exc
    return JSONResponse(
        status_code=404,
        content={"detail": f"Exchange rate for {exc.currency_code} is not available."},
    )


async def deal_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DealNotFoundError):
        raise exc
    return JSONResponse(
        status_code=404, content={"detail": f"Transaction {exc.deal_id} not found."}
    )


async def deal_already_processed_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if not isinstance(exc, DealAlreadyProcessedError):
        raise exc
    return JSONResponse(
        status_code=409,
        content={
            "detail": f"Transaction {exc.deal_id} is already processed with status {exc.status}."
        },
    )


async def invalid_currency_pair_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if not isinstance(exc, InvalidCurrencyPairError):
        raise exc
    return JSONResponse(
        status_code=422,
        content={"detail": f"Cannot exchange {exc.source} to {exc.target}."},
    )


async def invalid_amount_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


async def external_api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ExternalAPIError):
        raise exc
    logger.warning("Exchange rates unavailable: %s", exc.message)
    return JSONResponse(status_code=503, content={"detail": exc.message})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CurrencyNotFoundError, currency_not_found_handler)
    app.add_exception_handler(DealNotFoundError, deal_not_found_handler)
    app.add_exception_handler(DealAlreadyProcessedError, deal_already_processed_handler)
    app.add_exception_handler(InvalidCurrencyPairError, invalid_currency_pair_handler)
    app.add_exception_handler(InvalidAmountError, invalid_amount_handler)
    app.add_exception_handler(ExternalAPIError, external_api_error_handler)
