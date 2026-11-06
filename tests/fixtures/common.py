import os
from unittest.mock import MagicMock, AsyncMock
from zoneinfo import ZoneInfo
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4, UUID

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
from sqlalchemy import text
from httpx import ASGITransport, AsyncClient

from drivers.rest.routers.exchange import get_exchange_service
from persistence.models import (
    ExchangeTransaction,
    TransactionStatus,
    ExchangeRate,
    Base,
)
from services.exchange import ExchangeService
from drivers.rest.main import app
from persistence.uow import SQLAlchemyUnitOfWork


@pytest.fixture
def rates() -> list[ExchangeRate]:
    return [
        ExchangeRate(
            currency_code="USD", scale=1, rate=Decimal("3"), rate_date=date(2026, 1, 1)
        ),
        ExchangeRate(
            currency_code="EUR", scale=1, rate=Decimal("4"), rate_date=date(2026, 1, 1)
        ),
        ExchangeRate(
            currency_code="RUB",
            scale=100,
            rate=Decimal("3.5"),
            rate_date=date(2026, 1, 1),
        ),
    ]


@pytest.fixture
def deals() -> list[ExchangeTransaction]:
    updated_at = datetime(2026, 1, 2, 12, tzinfo=ZoneInfo("Europe/Minsk"))
    rows = [
        (1, "USD", "BYN", "100.00", "300.00", TransactionStatus.PENDING),
        (2, "USD", "BYN", "10.00", "30.00", TransactionStatus.COMPLETED),
        (3, "BYN", "USD", "15.00", "5.00", TransactionStatus.COMPLETED),
        (4, "EUR", "BYN", "50.00", "200.00", TransactionStatus.REJECTED),
    ]
    return [
        ExchangeTransaction(
            id=UUID(int=number),
            source_currency=source,
            target_currency=target,
            source_amount=Decimal(amount),
            target_amount=Decimal(result),
            exchange_rate=(Decimal(result) / Decimal(amount)).quantize(
                Decimal("0.000000000001")
            ),
            status=status,
            created_at=updated_at,
            updated_at=updated_at,
        )
        for number, source, target, amount, result, status in rows
    ]


@pytest.fixture
def uow(rates, deals):
    work = MagicMock()
    work.__aenter__ = AsyncMock(return_value=work)
    work.__aexit__ = AsyncMock(return_value=False)
    work.rates.get_latest_date = AsyncMock(return_value=date(2026, 1, 1))

    work.rates.get_all_by_date = AsyncMock(return_value=rates)
    work.transactions.get_by_id = AsyncMock(
        side_effect=lambda deal_id, for_update=False: next(
            (deal for deal in deals if deal.id == deal_id), None
        )
    )
    work.transactions.get_pending_deals = AsyncMock(
        side_effect=lambda: [
            deal for deal in deals if deal.status == TransactionStatus.PENDING
        ]
    )

    work.transactions.add.side_effect = deals.append
    return work


@pytest.fixture
def client(uow):
    overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_exchange_service] = lambda: ExchangeService(
        lambda: uow
    )

    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session_factory():
    url = os.getenv("TEST_DB_URL")
    schema = "test_exchange_" + uuid4().hex
    admin = create_async_engine(url)
    engine = create_async_engine(
        url, connect_args={"server_settings": {"search_path": schema}}
    )
    try:
        async with admin.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()
        try:
            async with admin.begin() as connection:
                await connection.execute(
                    text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                )

        finally:
            await admin.dispose()


@pytest.fixture
async def db_client(db_session_factory, rates, deals):
    async with db_session_factory.begin() as session:
        session.add_all(rates + deals)

    overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_exchange_service] = lambda: ExchangeService(
        lambda: SQLAlchemyUnitOfWork(db_session_factory)
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)
