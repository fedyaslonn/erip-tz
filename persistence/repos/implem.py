import uuid
from collections import defaultdict
from zoneinfo import ZoneInfo
from datetime import timedelta, datetime, time, date
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from domain.schemas.stats import CurrencyAggregatedStats
from persistence.models import ExchangeTransaction, TransactionStatus, ExchangeRate


class RateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_date(
        self, rate_date: date, currency_code: str
    ) -> ExchangeRate | None:
        result = await self.session.execute(
            select(ExchangeRate).where(
                ExchangeRate.rate_date == rate_date,
                ExchangeRate.currency_code == currency_code,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_date(self, rate_date: date) -> list[ExchangeRate]:
        result = await self.session.execute(
            select(ExchangeRate).where(ExchangeRate.rate_date == rate_date)
        )
        return list(result.scalars().all())

    async def get_latest_date(self, today: date) -> date | None:
        result = await self.session.execute(
            select(func.max(ExchangeRate.rate_date)).where(
                ExchangeRate.rate_date <= today
            )
        )
        return result.scalar_one_or_none()

    async def save_daily(self, rates: list[dict]) -> None:
        stmt = (
            insert(ExchangeRate)
            .values(rates)
            .on_conflict_do_nothing(constraint="uq_currency_rate_date")
        )
        await self.session.execute(stmt)

    def add(self, rate: ExchangeRate) -> None:
        self.session.add(rate)

    def add_all(self, rates: list[ExchangeRate]) -> None:
        self.session.add_all(rates)


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self, deal_id: uuid.UUID, for_update: bool = False
    ) -> ExchangeTransaction | None:
        stmt = select(ExchangeTransaction).where(ExchangeTransaction.id == deal_id)
        if for_update:
            stmt = stmt.with_for_update()

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_deals(self) -> list[ExchangeTransaction]:
        stmt = (
            select(ExchangeTransaction)
            .where(ExchangeTransaction.status == TransactionStatus.PENDING)
            .order_by(ExchangeTransaction.created_at, ExchangeTransaction.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_stats(
        self, date_from: date, date_to: date, currency: str | None = None
    ) -> list[CurrencyAggregatedStats]:
        zone = ZoneInfo("Europe/Minsk")
        start = datetime.combine(date_from, time.min, zone)

        end = datetime.combine(date_to + timedelta(days=1), time.min, zone)
        conditions = [
            ExchangeTransaction.status == TransactionStatus.COMPLETED,
            ExchangeTransaction.updated_at >= start,
            ExchangeTransaction.updated_at < end,
        ]

        if currency:
            conditions.append(
                or_(
                    ExchangeTransaction.source_currency == currency,
                    ExchangeTransaction.target_currency == currency,
                )
            )

        stmt = select(
            ExchangeTransaction.source_currency,
            ExchangeTransaction.source_amount,
            ExchangeTransaction.target_currency,
            ExchangeTransaction.target_amount,
        ).where(*conditions)

        result = await self.session.execute(stmt)

        stats = defaultdict(
            lambda: {
                "total_received": Decimal("0.00"),
                "total_spent": Decimal("0.00"),
                "deals_count": 0,
            }
        )

        for src_curr, src_amount, tgt_curr, tgt_amount in result:
            stats[src_curr]["total_received"] += src_amount
            stats[src_curr]["deals_count"] += 1

            stats[tgt_curr]["total_spent"] += tgt_amount
            stats[tgt_curr]["deals_count"] += 1

        if currency:
            stats = {k: v for k, v in stats.items() if k == currency}

        return [
            CurrencyAggregatedStats(currency=curr, **data)
            for curr, data in stats.items()
        ]

    def add(self, transaction: ExchangeTransaction) -> None:
        self.session.add(transaction)
