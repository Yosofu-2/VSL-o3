"""Statistics API endpoints for library analytics."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import Book, BookCopy, Reader, BorrowingRecord, Category

router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("/library")
async def get_library_stats(db: AsyncSession = Depends(get_db)):
    """Get overall library statistics."""
    total_books = (await db.execute(select(func.count(Book.id)))).scalar() or 0
    total_categories = (await db.execute(select(func.count(Category.id)))).scalar() or 0
    total_readers = (await db.execute(select(func.count(Reader.id)))).scalar() or 0
    total_copies = (await db.execute(select(func.sum(Book.total_copies)))).scalar() or 0
    available_copies = (await db.execute(select(func.sum(Book.available_copies)))).scalar() or 0
    borrowed = total_copies - available_copies

    # Overdue count
    now = datetime.now()
    overdue = (await db.execute(
        select(func.count(BorrowingRecord.id)).where(
            and_(
                BorrowingRecord.status.in_(["借出", "待确认"]),
                BorrowingRecord.due_date < now
            )
        )
    )).scalar() or 0

    # Due soon (within 7 days)
    due_soon = (await db.execute(
        select(func.count(BorrowingRecord.id)).where(
            and_(
                BorrowingRecord.status == "借出",
                BorrowingRecord.due_date >= now,
                BorrowingRecord.due_date <= now + timedelta(days=7)
            )
        )
    )).scalar() or 0

    return {
        "total_books": total_books,
        "total_categories": total_categories,
        "total_readers": total_readers,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "borrowed": borrowed,
        "overdue": overdue,
        "due_soon": due_soon,
    }


@router.get("/books-by-category")
async def get_books_by_category(db: AsyncSession = Depends(get_db)):
    """Get book count by category (bar chart)."""
    result = await db.execute(
        select(Category.name, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(func.count(Book.id).desc())
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [r[0] or "未分类" for r in rows],
        "values": [r[1] for r in rows],
    }


@router.get("/books-by-year")
async def get_books_by_year(db: AsyncSession = Depends(get_db)):
    """Get book count by publication year (line chart)."""
    result = await db.execute(
        select(
            extract('year', Book.publication_date).label('year'),
            func.count(Book.id)
        )
        .where(Book.publication_date.isnot(None))
        .group_by('year')
        .order_by('year')
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [str(int(r[0])) for r in rows],
        "values": [r[1] for r in rows],
    }


@router.get("/borrowing-trend")
async def get_borrowing_trend(db: AsyncSession = Depends(get_db)):
    """Get monthly borrowing trend for the last 12 months (line chart)."""
    now = datetime.now()
    twelve_months_ago = now - timedelta(days=365)

    result = await db.execute(
        select(
            func.strftime('%Y-%m', BorrowingRecord.borrow_date).label('month'),
            func.count(BorrowingRecord.id)
        )
        .where(BorrowingRecord.borrow_date >= twelve_months_ago)
        .group_by('month')
        .order_by('month')
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
    }


@router.get("/reader-activity")
async def get_reader_activity(db: AsyncSession = Depends(get_db)):
    """Get top 20 most active readers (bar chart)."""
    result = await db.execute(
        select(Reader.name, func.count(BorrowingRecord.id).label('count'))
        .join(BorrowingRecord, BorrowingRecord.reader_id == Reader.id)
        .group_by(Reader.id, Reader.name)
        .order_by(func.count(BorrowingRecord.id).desc())
        .limit(20)
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
    }


@router.get("/top-books")
async def get_top_books(db: AsyncSession = Depends(get_db)):
    """Get top 20 most borrowed books (bar chart)."""
    result = await db.execute(
        select(Book.title, func.count(BorrowingRecord.id).label('count'))
        .join(BookCopy, BorrowingRecord.copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .group_by(Book.id, Book.title)
        .order_by(func.count(BorrowingRecord.id).desc())
        .limit(20)
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [r[0][:30] for r in rows],
        "values": [r[1] for r in rows],
    }


@router.get("/genre-distribution")
async def get_genre_distribution(db: AsyncSession = Depends(get_db)):
    """Get book count by genre (pie chart)."""
    result = await db.execute(
        select(Book.genre, func.count(Book.id))
        .where(Book.genre.isnot(None))
        .group_by(Book.genre)
        .order_by(func.count(Book.id).desc())
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
    }


@router.get("/language-distribution")
async def get_language_distribution(db: AsyncSession = Depends(get_db)):
    """Get book count by language (pie chart)."""
    result = await db.execute(
        select(Book.language, func.count(Book.id))
        .where(Book.language.isnot(None))
        .group_by(Book.language)
        .order_by(func.count(Book.id).desc())
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
    }


@router.get("/overdue-analysis")
async def get_overdue_analysis(db: AsyncSession = Depends(get_db)):
    """Get overdue borrowing analysis."""
    now = datetime.now()

    # Overdue records - join through BookCopy since BorrowingRecord has copy_id, not book_id
    overdue_result = await db.execute(
        select(
            Reader.name.label('reader_name'),
            Book.title.label('book_title'),
            BorrowingRecord.borrow_date,
            BorrowingRecord.due_date,
            BorrowingRecord.status
        )
        .join(Reader, BorrowingRecord.reader_id == Reader.id)
        .join(BookCopy, BorrowingRecord.copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(
            and_(
                BorrowingRecord.status.in_(["借出", "待确认"]),
                BorrowingRecord.due_date < now
            )
        )
        .order_by(BorrowingRecord.due_date.asc())
    )
    overdue_rows = overdue_result.all()

    total_overdue = len(overdue_rows)
    total_fine = sum(
        max(0, (now - r.due_date).days) * 0.1 for r in overdue_rows
    )

    return {
        "total_overdue": total_overdue,
        "estimated_fine": round(total_fine, 2),
        "records": [
            {
                "reader": r.reader_name,
                "book": r.book_title,
                "borrow_date": r.borrow_date.strftime('%Y-%m-%d') if r.borrow_date else "",
                "due_date": r.due_date.strftime('%Y-%m-%d') if r.due_date else "",
                "days_overdue": max(0, (now - r.due_date).days),
                "fine": round(max(0, (now - r.due_date).days) * 0.1, 2),
            }
            for r in overdue_rows[:50]
        ]
    }


@router.get("/status-distribution")
async def get_status_distribution(db: AsyncSession = Depends(get_db)):
    """Get borrowing status distribution (pie chart)."""
    result = await db.execute(
        select(BorrowingRecord.status, func.count(BorrowingRecord.id))
        .group_by(BorrowingRecord.status)
        .order_by(func.count(BorrowingRecord.id).desc())
    )
    rows = result.all()
    if not rows:
        return {"labels": [], "values": []}
    return {
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
    }
