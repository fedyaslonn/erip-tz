import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from dotenv import load_dotenv

from drivers.rest.exception_handlers import register_exception_handlers
from drivers.rest.routers.exchange import router
from utils.nbrb_fetch import sync_daily_rates_task
from persistence.db import engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    load_dotenv()
    executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="nbrb_http_worker")
    scheduler = AsyncIOScheduler(timezone="Europe/Minsk")
    try:
        await sync_daily_rates_task(executor)
        scheduler.add_job(
            sync_daily_rates_task,
            trigger="cron",
            hour=0,
            minute=5,
            args=[executor],
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=True)
            await asyncio.sleep(0)
        await asyncio.to_thread(executor.shutdown, wait=True, cancel_futures=True)
        await engine.dispose()


app = FastAPI(title="Currency Exchange API", version="1.0.0", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(router)
