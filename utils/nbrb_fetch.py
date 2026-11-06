import urllib.request
import logging
import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from domain.schemas.nbrb import NBRBRateSchema
from persistence.uow import SQLAlchemyUnitOfWork
from persistence.db import async_session_maker

logger = logging.getLogger(__name__)


def fetch_nbrb_rates_sync(rate_date: date) -> list[dict]:
    base_url = os.getenv("NBRB_API_URL")

    url = f"{base_url}?periodicity=0&ondate={rate_date.isoformat()}"

    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"), parse_float=Decimal)

    if not isinstance(data, list) or not data:
        raise ValueError("NBRB returned an empty or invalid rate list")

    rates = [NBRBRateSchema.model_validate(item) for item in data]
    if any(rate.date.date() != rate_date for rate in rates):
        raise ValueError("NBRB returned rates for a different date")

    if len({rate.cur_abbr for rate in rates}) != len(rates):
        raise ValueError("NBRB returned duplicate currencies")

    return [
        dict(
            currency_code=rate.cur_abbr,
            scale=rate.cur_scale,
            rate=rate.cur_offrate,
            rate_date=rate_date,
        )
        for rate in rates
    ]


async def sync_daily_rates_task(executor: ThreadPoolExecutor) -> None:
    rate_date = datetime.now(ZoneInfo("Europe/Minsk")).date()
    try:
        rates = await asyncio.get_running_loop().run_in_executor(
            executor, fetch_nbrb_rates_sync, rate_date
        )

        async with SQLAlchemyUnitOfWork(async_session_maker) as uow:
            await uow.rates.save_daily(rates)

        logger.info("Saved %s NBRB rates for %s", len(rates), rate_date)

    except (OSError, ValueError, SQLAlchemyError):
        logger.exception("Could not synchronize NBRB rates for %s", rate_date)
