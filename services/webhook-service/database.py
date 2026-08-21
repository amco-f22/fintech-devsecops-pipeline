"""
Async database layer using SQLAlchemy 2.0.
Supports SQLite (local dev) and PostgreSQL (production/K8s).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class TransactionRecord(Base):
    """
    Persisted transaction webhook record.
    Indexed on transaction_id for idempotency checks.
    """
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    transaction_id = Column(String(64), nullable=False, unique=True, index=True)
    merchant_id = Column(String(32), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(String(20), nullable=False)
    payment_method = Column(String(20), nullable=False)
    customer_email = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_merchant_status", "merchant_id", "status"),
    )


# --- Engine & Session Factory ---

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency: yield an async database session."""
    async with async_session_factory() as session:
        yield session


async def find_transaction(session: AsyncSession, transaction_id: str) -> Optional[TransactionRecord]:
    """Look up a transaction by its external ID (idempotency check)."""
    result = await session.execute(
        select(TransactionRecord).where(
            TransactionRecord.transaction_id == transaction_id
        )
    )
    return result.scalar_one_or_none()


async def store_transaction(
    session: AsyncSession,
    transaction_id: str,
    merchant_id: str,
    amount: Decimal,
    currency: str,
    status: str,
    payment_method: str,
    customer_email: Optional[str] = None,
    metadata_json: Optional[str] = None,
) -> TransactionRecord:
    """Persist a new transaction record."""
    record = TransactionRecord(
        transaction_id=transaction_id,
        merchant_id=merchant_id,
        amount=amount,
        currency=currency,
        status=status,
        payment_method=payment_method,
        customer_email=customer_email,
        metadata_json=metadata_json,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record
