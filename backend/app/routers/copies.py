"""Copies router. English keys, cascade handled by model."""

import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import Book, BookCopy
from app.security import get_current_admin

router = APIRouter(prefix="/api/copies", tags=["copies"])


class CopyCreate(BaseModel):
    book_id: int
    asset_number: str | None = None
    status: str | None = "在馆"
    shelf: str | None = None


@router.get("/")
async def list_copies(
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    result = await db.execute(select(BookCopy).order_by(BookCopy.id))
    rows = result.scalars().all()
    return {"data": [{"id": r.id, "book_id": r.book_id, "asset_number": r.asset_number,
                       "entry_date": str(r.entry_date) if r.entry_date else "",
                       "status": r.status, "shelf": r.shelf} for r in rows],
            "total": len(rows)}


@router.post("/")
async def create_copy(
    body: CopyCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    book = await db.get(Book, body.book_id)
    if not book:
        raise HTTPException(404, "图书不存在")
    copy = BookCopy(
        book_id=body.book_id,
        asset_number=body.asset_number,
        entry_date=datetime.date.today(),
        status=body.status or "在馆",
        shelf=body.shelf,
    )
    db.add(copy)
    await db.commit()
    await db.refresh(copy)
    return {"id": copy.id, "message": "添加成功"}


@router.delete("/{copy_id}")
async def delete_copy(
    copy_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    copy = await db.get(BookCopy, copy_id)
    if not copy:
        raise HTTPException(404, "单册不存在")
    # Cascade handled by model
    await db.delete(copy)
    await db.commit()
    return {"message": "删除成功"}
