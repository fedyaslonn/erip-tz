from typing import Protocol
from types import TracebackType

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from persistence.repos.protocols import (
    ITransactionRepository,
    IRateRepository,
)
from persistence.repos.implem import (
    TransactionRepository,
    RateRepository,
)


class IUnitOfWork(Protocol):
    rates: IRateRepository
    transactions: ITransactionRepository

    async def __aenter__(self) -> "IUnitOfWork": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class SQLAlchemyUnitOfWork:
    rates: IRateRepository
    transactions: ITransactionRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.rates = RateRepository(self.session)
        self.transactions = TransactionRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                try:
                    await self.commit()
                except BaseException:
                    await self.rollback()
                    raise
        finally:
            await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
