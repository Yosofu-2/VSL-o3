# -*- coding: utf-8 -*-
"""Common utility functions shared across the application."""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_json(text: str) -> Optional[dict]:
    """Extract the first valid JSON object from a text string.

    Handles cases where LLM responses contain JSON embedded in
    markdown code blocks or other surrounding text.

    Args:
        text: Raw text that may contain a JSON object.

    Returns:
        Parsed dict if found, None otherwise.
    """
    if not text:
        return None

    try:
        start = text.index("{")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
    except (ValueError, json.JSONDecodeError):
        pass
    return None


def safe_str(value, default: str = "") -> str:
    """Convert a value to string safely, handling None and empty values."""
    if value is None:
        return default
    return str(value)


def parse_int_field(value, default: Optional[int] = None) -> Optional[int]:
    """Parse an integer field from Excel data (handles float/int/str)."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_float_field(value, default: Optional[float] = None) -> Optional[float]:
    """Parse a float field from Excel data."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate(text: str, max_length: int = 64) -> str:
    """Truncate text to a maximum length."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length]


def build_like(value: str) -> str:
    """Build a SQL LIKE pattern with wildcards."""
    return f"%{value}%"


def format_book_info(book) -> str:
    """Format a book object into a readable string for LLM context."""
    cat_name = book.category.name if book.category else "-"
    return (
        f"[{book.id}] {book.title}\n"
        f"  Author: {book.authors or '-'} | ISBN: {book.isbn or '-'}\n"
        f"  Category: {cat_name} | Call#: {book.call_number or '-'}\n"
        f"  Publisher: {book.publisher or '-'} | Year: {book.publication_year or '-'}\n"
        f"  Copies: {book.total_copies or 0} Available: {book.available_copies or 0}"
    )


def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def classify_borrowing_status(record) -> str:
    """Classify a borrowing record into 借出/临期未还/逾期未还/已归还/待确认."""
    import datetime
    if record.status == "已归还":
        return "已归还"
    if record.status == "待确认":
        return "待确认"
    if not record.due_date:
        return "借出"
    today = datetime.date.today()
    days_left = (record.due_date - today).days
    if days_left < 0:
        return "逾期未还"
    if days_left <= 3:
        return "临期未还"
    return "借出"


async def log_audit(db, user_id, user_type, action, resource_type, resource_id=None, details=None, ip_address=None):
    """Create an audit log entry."""
    from app.models.model import AuditLog
    import json
    log = AuditLog(
        user_id=user_id,
        user_type=user_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()


async def create_notification(db, user_id, user_type, notif_type, title, content=None, related_id=None):
    """Create a notification for a user."""
    from app.models.model import Notification
    notif = Notification(
        user_id=user_id,
        user_type=user_type,
        type=notif_type,
        title=title,
        content=content,
        related_id=related_id,
    )
    db.add(notif)
    await db.commit()
    return notif
