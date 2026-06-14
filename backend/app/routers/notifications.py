# -*- coding: utf-8 -*-
"""Notification router. CRUD endpoints for persistent notifications."""

import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: int
    user_id: int
    user_type: str
    type: str
    title: str
    content: str | None = None
    is_read: int
    related_id: int | None = None
    created_at: str
    read_at: str | None = None


def _notif_to_dict(n: Notification) -> dict:
    return {
        "id": n.id,
        "user_id": n.user_id,
        "user_type": n.user_type,
        "type": n.type,
        "title": n.title,
        "content": n.content,
        "is_read": n.is_read,
        "related_id": n.related_id,
        "created_at": str(n.created_at) if n.created_at else "",
        "read_at": str(n.read_at) if n.read_at else None,
    }


@router.get("/")
async def list_notifications(
    user_id: int,
    user_type: str = "reader",
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List notifications for a user, newest first."""
    query = (
        select(Notification)
        .where(Notification.user_id == user_id, Notification.user_type == user_type)
        .order_by(Notification.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.scalars().all()
    data = [_notif_to_dict(n) for n in rows]
    return {"data": data, "total": len(data)}


@router.get("/unread-count")
async def get_unread_count(
    user_id: int,
    user_type: str = "reader",
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count for a user."""
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.user_type == user_type,
            Notification.is_read == 0,
        )
    )
    count = result.scalar() or 0
    return {"count": count}


@router.put("/{notif_id}/read")
async def mark_notification_read(notif_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a single notification as read."""
    notif = await db.get(Notification, notif_id)
    if not notif:
        raise HTTPException(404, "通知不存在")
    notif.is_read = 1
    notif.read_at = datetime.datetime.now()
    await db.commit()
    return {"message": "已标记为已读"}


@router.put("/read-all")
async def mark_all_read(
    user_id: int,
    user_type: str = "reader",
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for a user."""
    now = datetime.datetime.now()
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.user_type == user_type,
            Notification.is_read == 0,
        )
        .values(is_read=1, read_at=now)
    )
    await db.commit()
    return {"message": "全部标记为已读"}


@router.delete("/{notif_id}")
async def delete_notification(notif_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a notification."""
    notif = await db.get(Notification, notif_id)
    if not notif:
        raise HTTPException(404, "通知不存在")
    await db.delete(notif)
    await db.commit()
    return {"message": "已删除"}
