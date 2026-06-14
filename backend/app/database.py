"""Database setup with async SQLAlchemy + SQLite."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, inspect
import logging

import os

from app.config import settings
from app.utils import setup_logging

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

_db_path = os.environ.get("LITMAN_DB_PATH")
if _db_path:
    _db_url = f"sqlite+aiosqlite:///{_db_path}"
else:
    _db_url = settings.database_url

# Configure connection pool for SQLite
# SQLite doesn't support connection pooling in the traditional sense,
# but we configure pool_pre_ping for connection health checks
engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in _db_url else {},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency that provides a database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def _migrate_columns(conn):
    """Add missing columns to existing tables (SQLite doesn't support ALTER TABLE ADD COLUMN for all types)."""
    from app.models.model import Book, Reader, BorrowingRecord, Category, BookCopy, Admin, AuditLog, LLMModel, Conversation, Message, Attachment, Reservation, Notification, Fine

    # Define expected columns for each table
    table_columns = {
        "borrowing_records": [
            ("renewed", "INTEGER DEFAULT 0"),
        ],
        "books": [
            ("genre", "VARCHAR(64)"),
            ("language", "VARCHAR(16)"),
            ("pages", "INTEGER"),
            ("price", "REAL"),
            ("binding", "VARCHAR(32)"),
            ("description", "TEXT"),
        ],
        "readers": [
            ("phone", "VARCHAR(32)"),
            ("department", "VARCHAR(64)"),
            ("max_borrow", "INTEGER DEFAULT 5"),
            ("borrow_days", "INTEGER DEFAULT 30"),
            ("password_hash", "VARCHAR(256)"),
        ],
        "book_categories": [
            ("parent_id", "INTEGER"),
        ],
        "book_copies": [
            ("location", "VARCHAR(128)"),
            ("condition", "VARCHAR(32)"),
            ("notes", "TEXT"),
        ],
        "notifications": [
            ("is_read", "BOOLEAN DEFAULT 0"),
            ("user_type", "VARCHAR(16) DEFAULT 'reader'"),
        ],
        "reservations": [
            ("status", "VARCHAR(16) DEFAULT 'pending'"),
            ("expire_date", "DATE"),
        ],
        "fines": [
            ("paid", "BOOLEAN DEFAULT 0"),
            ("paid_date", "DATE"),
        ],
        "audit_logs": [
            ("ip_address", "VARCHAR(64)"),
            ("user_agent", "VARCHAR(256)"),
        ],
        "llm_models": [
            ("api_key_encrypted", "TEXT"),
            ("base_url", "VARCHAR(512)"),
            ("model_type", "VARCHAR(32) DEFAULT 'openai'"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("max_tokens", "INTEGER DEFAULT 4096"),
            ("temperature", "REAL DEFAULT 0.7"),
        ],
    }

    for table_name, columns in table_columns.items():
        # Get existing columns
        result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
        existing = {row[1] for row in result.fetchall()}

        for col_name, col_type in columns:
            if col_name not in existing:
                try:
                    await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"Added column {col_name} to {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to add column {col_name} to {table_name}: {e}")


async def init_db():
    """Initialize database tables and run migrations."""
    async with engine.begin() as conn:
        from app.models import model  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_columns(conn)
