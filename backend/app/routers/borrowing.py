"""Borrowing router. Supports borrow/return by book title or ID, pending-confirmation return flow."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.model import Book, BookCopy, BorrowingRecord, Reader
from app.utils import classify_borrowing_status, log_audit, create_notification
from app.security import get_current_admin, get_current_user

router = APIRouter(prefix="/api/borrowing", tags=["borrowing"])

# ── Borrowing rules by identity type ──────────────────────
# Format: {identity_type: (borrow_days, max_borrow_count)}
BORROW_RULES = {
    "学生": (30, 3),
    "教师": (180, 5),
}
DEFAULT_BORROW_DAYS = 30
DEFAULT_MAX_BORROW = 10


def get_borrow_rules(reader: Reader) -> tuple[int, int]:
    """Get borrow days and max borrow count based on reader's identity type."""
    identity = reader.identity_type or ""
    if identity in BORROW_RULES:
        return BORROW_RULES[identity]
    # Fallback to reader's max_borrow field or default
    max_borrow = reader.max_borrow or DEFAULT_MAX_BORROW
    return (DEFAULT_BORROW_DAYS, max_borrow)


# ── Request schemas ───────────────────────────────────────

class BorrowRequest(BaseModel):
    reader_id: int
    copy_id: int | None = None        # borrow by specific copy
    book_id: int | None = None        # borrow by book (auto-pick first available copy)
    book_title: str | None = None     # borrow by book title (auto-pick first available copy)


class ReturnRequest(BaseModel):
    copy_id: int | None = None
    book_id: int | None = None
    book_title: str | None = None
    reader_id: int | None = None      # optional: specify which reader's record to return


class ConfirmReturnRequest(BaseModel):
    record_id: int


# ── Helpers ────────────────────────────────────────────────

def _record_to_dict(r: BorrowingRecord, reader_name: str = "", book_title: str = "") -> dict:
    return {
        "id": r.id,
        "reader_id": r.reader_id,
        "reader_name": reader_name,
        "copy_id": r.copy_id,
        "book_title": book_title,
        "borrow_date": str(r.borrow_date) if r.borrow_date else "",
        "due_date": str(r.due_date) if r.due_date else "",
        "return_date": str(r.return_date) if r.return_date else "",
        "overdue_days": r.overdue_days,
        "status": r.status,
        "classified_status": classify_borrowing_status(r),
        "renewed": r.renewed if hasattr(r, "renewed") else 0,
    }


async def _resolve_book_title(db: AsyncSession, book_id: int) -> str:
    book = await db.get(Book, book_id)
    return book.title if book else ""


async def _resolve_reader_name(db: AsyncSession, reader_id: int) -> str:
    reader = await db.get(Reader, reader_id)
    return reader.name if reader else ""


# ── Endpoints ──────────────────────────────────────────────

@router.get("/")
async def list_borrowing(
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """List all borrowing records with classified status."""
    result = await db.execute(
        select(BorrowingRecord)
        .options(
            selectinload(BorrowingRecord.reader),
            selectinload(BorrowingRecord.copy).selectinload(BookCopy.book)
        )
        .order_by(BorrowingRecord.id.desc())
    )
    rows = result.scalars().all()

    data = []
    today = datetime.date.today()
    three_days_ago = today - datetime.timedelta(days=3)

    for r in rows:
        reader_name = r.reader.name if r.reader else ""
        book_title = r.copy.book.title if r.copy and r.copy.book else ""
        data.append(_record_to_dict(r, reader_name, book_title))

        # Check for overdue books and create notifications if not notified recently
        if r.status in ["借出", "临期未还", "逾期未还"] and r.due_date and r.due_date < today:
            # Check if we already notified this reader in the last 3 days
            from app.models.model import Notification
            notif_result = await db.execute(
                select(Notification).where(
                    Notification.user_id == r.reader_id,
                    Notification.user_type == "reader",
                    Notification.type == "overdue",
                    Notification.related_id == r.id,
                    Notification.created_at >= three_days_ago
                ).limit(1)
            )
            existing_notif = notif_result.scalar_one_or_none()

            if not existing_notif:
                overdue_days = (today - r.due_date).days
                await create_notification(
                    db,
                    user_id=r.reader_id,
                    user_type="reader",
                    notif_type="overdue",
                    title="图书逾期提醒",
                    content=f"《{book_title}》已逾期 {overdue_days} 天，请尽快归还。",
                    related_id=r.id,
                )

    return {"data": data, "total": len(rows)}


@router.get("/stats")
async def borrowing_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get borrowing statistics: 借出/临期未还/逾期未还/已归还/待确认 counts."""
    result = await db.execute(select(BorrowingRecord))
    rows = result.scalars().all()

    stats = {"借出": 0, "临期未还": 0, "逾期未还": 0, "已归还": 0, "待确认": 0}
    for r in rows:
        cs = _classify_status(r)
        stats[cs] = stats.get(cs, 0) + 1

    return stats


@router.post("/borrow")
async def borrow_book(body: BorrowRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Borrow a book. Supports borrow by copy_id, book_id, or book_title."""
    reader = await db.get(Reader, body.reader_id)
    if not reader:
        raise HTTPException(404, "读者不存在")

    # Resolve which copy to borrow
    copy = None
    if body.copy_id:
        copy = await db.get(BookCopy, body.copy_id)
    elif body.book_id:
        # Pick first available copy of this book
        result = await db.execute(
            select(BookCopy).where(
                BookCopy.book_id == body.book_id,
                BookCopy.status == "在馆"
            ).limit(1)
        )
        copy = result.scalar_one_or_none()
    elif body.book_title:
        # Find book by title, then pick first available copy
        result = await db.execute(
            select(Book).where(Book.title == body.book_title).limit(1)
        )
        book = result.scalar_one_or_none()
        if book:
            result2 = await db.execute(
                select(BookCopy).where(
                    BookCopy.book_id == book.id,
                    BookCopy.status == "在馆"
                ).limit(1)
            )
            copy = result2.scalar_one_or_none()
    else:
        raise HTTPException(400, "请提供 copy_id、book_id 或 book_title")

    if not copy:
        raise HTTPException(404, "未找到可借的单册")
    if copy.status != "在馆":
        raise HTTPException(400, "该单册不可借")

    # Check borrow limit based on identity type
    borrow_days, max_borrow = get_borrow_rules(reader)
    current_borrowed = await db.execute(
        select(func.count(BorrowingRecord.id))
        .where(
            BorrowingRecord.reader_id == reader.id,
            BorrowingRecord.status.in_(["借出", "临期未还"])
        )
    )
    borrowed_count = current_borrowed.scalar() or 0
    if borrowed_count >= max_borrow:
        raise HTTPException(400, f"已达最大借阅数({max_borrow}本)，无法继续借阅")

    book = await db.get(Book, copy.book_id)
    borrow_date = datetime.date.today()
    due_date = borrow_date + datetime.timedelta(days=borrow_days)

    record = BorrowingRecord(
        reader_id=body.reader_id,
        copy_id=copy.id,
        borrow_date=borrow_date,
        due_date=due_date,
        status="借出",
    )
    copy.status = "借出"
    if book and book.available_copies and book.available_copies > 0:
        book.available_copies -= 1
        if book.available_copies == 0:
            book.status = "借出"

    db.add(record)
    await db.commit()

    # Log audit
    await log_audit(
        db=db,
        user_id=body.reader_id,
        user_type="reader",
        action="borrow",
        resource_type="borrowing",
        resource_id=record.id,
        details={"book_id": copy.book_id, "copy_id": copy.id, "due_date": str(due_date)},
        ip_address=request.client.host if request.client else None
    )

    return {"message": "借书成功", "due_date": str(due_date), "copy_id": copy.id}


@router.post("/return")
async def return_book(
    body: ReturnRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Request return. Sets status to 待确认 (pending admin confirmation)."""
    # Find the active borrowing record
    query = select(BorrowingRecord).where(
        BorrowingRecord.status.in_(["借出", "临期未还", "逾期未还"])
    )
    if body.copy_id:
        query = query.where(BorrowingRecord.copy_id == body.copy_id)
    if body.reader_id:
        query = query.where(BorrowingRecord.reader_id == body.reader_id)
    if body.book_id:
        # Find copies of this book
        copies_result = await db.execute(
            select(BookCopy.id).where(BookCopy.book_id == body.book_id)
        )
        copy_ids = [c[0] for c in copies_result.all()]
        if copy_ids:
            query = query.where(BorrowingRecord.copy_id.in_(copy_ids))
    if body.book_title:
        books_result = await db.execute(
            select(Book.id).where(Book.title == body.book_title)
        )
        book_ids = [b[0] for b in books_result.all()]
        if book_ids:
            copies_result = await db.execute(
                select(BookCopy.id).where(BookCopy.book_id.in_(book_ids))
            )
            copy_ids = [c[0] for c in copies_result.all()]
            if copy_ids:
                query = query.where(BorrowingRecord.copy_id.in_(copy_ids))

    query = query.order_by(BorrowingRecord.id.desc()).limit(1)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(404, "未找到借阅记录")

    # Set to pending confirmation (do NOT change copy status yet)
    record.status = "待确认"
    await db.commit()

    # Log audit
    await log_audit(
        db=db,
        user_id=current_user["id"],
        user_type=current_user["type"],
        action="return_request",
        resource_type="borrowing",
        resource_id=record.id,
        details={"copy_id": record.copy_id, "reader_id": record.reader_id},
        ip_address=request.client.host if request.client else None
    )

    return {"message": "还书申请已提交，等待管理员确认", "record_id": record.id}


@router.post("/confirm-return")
async def confirm_return(
    body: ConfirmReturnRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Admin confirms a pending return. Finalizes the return process."""
    record = await db.get(BorrowingRecord, body.record_id)
    if not record:
        raise HTTPException(404, "借阅记录不存在")
    if record.status != "待确认":
        raise HTTPException(400, "该记录不是待确认状态")

    return_date = datetime.date.today()
    overdue = (return_date - record.due_date).days if record.due_date and return_date > record.due_date else 0
    record.return_date = return_date
    record.overdue_days = overdue
    record.status = "已归还"

    # Create fine if overdue
    fine_info = None
    if overdue > 0:
        fine_amount = round(overdue * 0.1, 2)
        from app.models.model import Fine
        fine = Fine(reader_id=record.reader_id, borrowing_id=record.id, amount=fine_amount, reason=f"逾期{overdue}天")
        db.add(fine)

    # Now actually return the copy
    copy = await db.get(BookCopy, record.copy_id)
    if copy:
        copy.status = "在馆"
        book = await db.get(Book, copy.book_id)
        if book:
            book.available_copies = (book.available_copies or 0) + 1
            book.status = "在馆"

            # Check for pending reservations
            from app.models.model import Reservation
            res_result = await db.execute(
                select(Reservation).where(Reservation.book_id == book.id, Reservation.status == "等待中").order_by(Reservation.id.asc())
            )
            reservations = res_result.scalars().all()
            if reservations:
                first_res = reservations[0]
                first_res.status = "已通知"
                first_res.notified_at = datetime.datetime.now()
                await create_notification(db, first_res.reader_id, "reader", "reservation_ready",
                    "预约图书已就绪", f"《{book.title}》已可借阅，请尽快前来借阅", first_res.id)

    await db.commit()

    # Log audit
    await log_audit(
        db=db,
        user_id=current_admin["id"],
        user_type="admin",
        action="confirm_return",
        resource_type="borrowing",
        resource_id=record.id,
        details={"reader_id": record.reader_id, "overdue_days": overdue},
        ip_address=request.client.host if request.client else None
    )

    # Create notification for reader
    book_title = ""
    if book:
        book_title = book.title
    msg = "还书确认成功"
    if overdue > 0:
        msg += f"，逾期 {overdue} 天"
    await create_notification(
        db,
        user_id=record.reader_id,
        user_type="reader",
        notif_type="return_confirmed",
        title="还书确认成功",
        content=f"《{book_title}》{msg}",
        related_id=record.id,
    )

    return {"message": msg, "fine_info": fine_info}


@router.post("/reject-return")
async def reject_return(
    body: ConfirmReturnRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Admin rejects a pending return. Reverts status back to 借出."""
    record = await db.get(BorrowingRecord, body.record_id)
    if not record:
        raise HTTPException(404, "借阅记录不存在")
    if record.status != "待确认":
        raise HTTPException(400, "该记录不是待确认状态")

    record.status = "借出"
    await db.commit()

    # Log audit
    await log_audit(
        db=db,
        user_id=current_admin["id"],
        user_type="admin",
        action="reject_return",
        resource_type="borrowing",
        resource_id=record.id,
        details={"reader_id": record.reader_id},
        ip_address=request.client.host if request.client else None
    )

    # Create notification for reader
    copy = await db.get(BookCopy, record.copy_id)
    book_title = ""
    if copy:
        book = await db.get(Book, copy.book_id)
        if book:
            book_title = book.title
    await create_notification(
        db,
        user_id=record.reader_id,
        user_type="reader",
        notif_type="return_rejected",
        title="还书申请被拒绝",
        content=f"《{book_title}》还书申请已被管理员拒绝，请联系管理员了解详情。",
        related_id=record.id,
    )

    return {"message": "已撤销还书申请"}


@router.get("/pending")
async def list_pending_returns(
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """List all borrowing records pending admin confirmation."""
    result = await db.execute(
        select(BorrowingRecord)
        .options(
            selectinload(BorrowingRecord.reader),
            selectinload(BorrowingRecord.copy).selectinload(BookCopy.book)
        )
        .where(
            BorrowingRecord.status == "待确认"
        )
        .order_by(BorrowingRecord.id.desc())
    )
    rows = result.scalars().all()

    data = []
    for r in rows:
        reader_name = r.reader.name if r.reader else ""
        book_title = r.copy.book.title if r.copy and r.copy.book else ""
        data.append(_record_to_dict(r, reader_name, book_title))

    return {"data": data, "total": len(rows)}


class RenewRequest(BaseModel):
    record_id: int


@router.post("/renew")
async def renew_book(body: RenewRequest, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    record = await db.get(BorrowingRecord, body.record_id)
    if not record:
        raise HTTPException(404, "借阅记录不存在")
    if record.status not in ["借出", "临期未还"]:
        raise HTTPException(400, "该记录无法续借")
    if record.renewed == 1:
        raise HTTPException(400, "已续借过，无法再次续借")
    today = datetime.date.today()
    if record.due_date and today > record.due_date:
        raise HTTPException(400, "已逾期，无法续借")

    # Get reader's identity type for renewal period
    reader = await db.get(Reader, record.reader_id)
    if not reader:
        raise HTTPException(404, "读者不存在")

    borrow_days, _ = get_borrow_rules(reader)
    # Renewal extends by half of the original borrowing period
    renew_days = max(borrow_days // 2, 7)  # At least 7 days
    new_due_date = record.due_date + datetime.timedelta(days=renew_days)
    record.due_date = new_due_date
    record.renewed = 1
    await db.commit()
    return {"message": "续借成功", "new_due_date": str(new_due_date)}
