# -*- coding: utf-8 -*-
"""Reservation router. CRUD endpoints for book reservations."""

import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.model import Reservation, Book, Reader, Notification
from app.utils import create_notification
from app.security import get_current_admin

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


class ReservationCreate(BaseModel):
    reader_id: int
    book_id: int


class ReservationOut(BaseModel):
    id: int
    reader_id: int
    book_id: int
    status: str
    created_at: str
    notified_at: str | None = None


def _reservation_to_dict(r: Reservation, reader_name: str = "", book_title: str = "") -> dict:
    return {
        "id": r.id,
        "reader_id": r.reader_id,
        "reader_name": reader_name,
        "book_id": r.book_id,
        "book_title": book_title,
        "status": r.status,
        "created_at": str(r.created_at) if r.created_at else "",
        "notified_at": str(r.notified_at) if r.notified_at else None,
    }


@router.post("")
async def create_reservation(
    body: ReservationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new reservation for a book."""
    # Verify reader and book exist
    reader = await db.get(Reader, body.reader_id)
    if not reader:
        raise HTTPException(404, "读者不存在")

    book = await db.get(Book, body.book_id)
    if not book:
        raise HTTPException(404, "图书不存在")

    # Check if reader already has a pending reservation for this book
    result = await db.execute(
        select(Reservation).where(
            Reservation.reader_id == body.reader_id,
            Reservation.book_id == body.book_id,
            Reservation.status.in_(["等待中", "已通知"])
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(400, "您已有该图书的预约")

    reservation = Reservation(
        reader_id=body.reader_id,
        book_id=body.book_id,
        status="等待中"
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)

    return {"message": "预约成功", "reservation_id": reservation.id}


@router.delete("/{reservation_id}")
async def cancel_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a reservation."""
    reservation = await db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(404, "预约不存在")

    if reservation.status not in ["等待中", "已通知"]:
        raise HTTPException(400, "该预约无法取消")

    reservation.status = "已取消"
    await db.commit()

    return {"message": "预约已取消"}


@router.get("/my")
async def get_my_reservations(
    reader_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all reservations for a reader."""
    result = await db.execute(
        select(Reservation)
        .options(
            selectinload(Reservation.reader),
            selectinload(Reservation.book)
        )
        .where(Reservation.reader_id == reader_id)
        .order_by(Reservation.id.desc())
    )
    reservations = result.scalars().all()

    data = []
    for r in reservations:
        reader_name = r.reader.name if r.reader else ""
        book_title = r.book.title if r.book else ""
        data.append(_reservation_to_dict(r, reader_name, book_title))

    return {"data": data, "total": len(data)}


@router.get("/book/{book_id}")
async def get_book_reservations(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all reservations for a book (admin only)."""
    result = await db.execute(
        select(Reservation)
        .options(
            selectinload(Reservation.reader),
            selectinload(Reservation.book)
        )
        .where(Reservation.book_id == book_id)
        .order_by(Reservation.id.asc())
    )
    reservations = result.scalars().all()

    data = []
    for r in reservations:
        reader_name = r.reader.name if r.reader else ""
        book_title = r.book.title if r.book else ""
        data.append(_reservation_to_dict(r, reader_name, book_title))

    return {"data": data, "total": len(data)}
