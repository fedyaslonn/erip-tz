import uuid
import enum
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, DeclarativeBase, Mapped
from sqlalchemy import (
    func,
    UniqueConstraint,
    DateTime,
    Numeric,
    Integer,
    String,
    Enum,
    Date,
)


class Base(DeclarativeBase):
    pass


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint("currency_code", "rate_date", name="uq_currency_rate_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    currency_code: Mapped[str] = mapped_column(String(3), index=True)
    scale: Mapped[int] = mapped_column(Integer)
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    rate_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ExchangeTransaction(Base):
    __tablename__ = "exchange_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_currency: Mapped[str] = mapped_column(String(3), index=True)
    target_currency: Mapped[str] = mapped_column(String(3), index=True)
    source_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"),
        default=TransactionStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
