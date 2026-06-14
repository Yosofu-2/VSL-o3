# -*- coding: utf-8 -*-
"""
LitManager DBAgent - strict tool-calling mode.
LLM outputs ONLY JSON tool calls (no natural language), saving tokens.
Handles natural language and fuzzy queries for book search, classification, and numbering.
"""

import json
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func as sa_func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.model import Admin, Book, BookCopy, BorrowingRecord, Category, LLMModel, Reader
from app.services.model_service import LLMClient
from app.services.web_search import web_search, search_book_info


TOOL_SYSTEM_PROMPT = """You are a library tool. Output ONLY JSON.

Format: {"tool":"name","args":{}}

Tools:
search_books - args: {"query":"text","limit":10}
list_readers - args: {}
list_borrowing - args: {}
count_statistics - args: {"group_by":"category"}
list_categories - args: {}
add_book - args: {"title":"name"}

Examples:
"列出图书" -> {"tool":"search_books","args":{"query":"","limit":100}}
"统计" -> {"tool":"count_statistics","args":{"group_by":"category"}}
"读者" -> {"tool":"list_readers","args":{}}
"搜索关于量子力学的书" -> {"tool":"search_books","args":{"query":"量子力学","limit":10}}

Output ONLY the JSON. No other text."""


async def _get_categories_context(db):
    result = await db.execute(select(Category).order_by(Category.id))
    cats = result.scalars().all()
    if not cats:
        return "No categories exist yet."
    return "Categories:\n" + "\n".join(
        f"  [{c.id}] {c.name} (code: {c.code or '-'})" for c in cats
    )


def _fmt_book(book):
    cat_name = book.category.name if book.category else "-"
    return (
        f"[{book.id}] {book.title}\n"
        f"  Author: {book.authors or '-'} | ISBN: {book.isbn or '-'}\n"
        f"  Category: {cat_name} | Call#: {book.call_number or '-'}\n"
        f"  Publisher: {book.publisher or '-'} | Year: {book.publication_year or '-'}\n"
        f"  Copies: {book.total_copies or 0} Available: {book.available_copies or 0}"
    )


async def _tool_search_books(query, limit, db):
    like = f"%{query}%"
    result = await db.execute(
        select(Book).options(selectinload(Book.category))
        .where(or_(
            Book.title.ilike(like), Book.authors.ilike(like),
            Book.publisher.ilike(like), Book.isbn.ilike(like)))
        .limit(limit)
    )
    items = result.scalars().all()
    if not items:
        return f"No books found matching '{query}'."
    return f"Found {len(items)} books:\n" + "\n\n".join(_fmt_book(b) for b in items)


async def _tool_get_book(id, db):
    result = await db.execute(
        select(Book).options(selectinload(Book.category)).where(Book.id == id)
    )
    book = result.scalar_one_or_none()
    return _fmt_book(book) if book else f"Book #{id} not found."


async def _tool_add_book(data, db):
    book = Book(
        title=data.get("title", ""),
        call_number=data.get("call_number"),
        authors=data.get("authors"),
        publisher=data.get("publisher"),
        publication_year=data.get("publication_year"),
        isbn=data.get("isbn"),
        category_id=data.get("category_id"),
        language=data.get("language"),
        pages=data.get("pages"),
        price=data.get("price"),
        location=data.get("location"),
        total_copies=data.get("total_copies", 1),
        available_copies=data.get("total_copies", 1),
        notes=data.get("notes"),
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    total = book.total_copies or 1
    for i in range(total):
        copy = BookCopy(book_id=book.id,
                        asset_number=f"{book.id}-{i+1:03d}",
                        status="在馆")
        db.add(copy)
    await db.commit()
    return f"Added book #{book.id}: {book.title} (Call#: {book.call_number or '-'})"


async def _tool_update_book(id, data, db):
    book = await db.get(Book, id)
    if not book:
        return f"Book #{id} not found."
    fields = ["title", "call_number", "authors", "publisher", "publication_year",
              "isbn", "category_id", "language", "pages", "price", "location",
              "total_copies", "available_copies", "status", "notes"]
    changed = []
    for f in fields:
        if f in data:
            setattr(book, f, data[f])
            changed.append(f)
    if changed:
        await db.commit()
    return f"Updated book #{id}: {', '.join(changed) if changed else 'no changes'}"


async def _tool_delete_book(id, db):
    book = await db.get(Book, id)
    if not book:
        return f"Book #{id} not found."
    title = book.title
    await db.delete(book)
    await db.commit()
    return f"Deleted book #{id}: {title}"


async def _tool_list_categories(db):
    result = await db.execute(select(Category).order_by(Category.id))
    cats = result.scalars().all()
    if not cats:
        return "No categories."
    lines = [f"Categories ({len(cats)}):"]
    for c in cats:
        p = f" (parent: {c.parent_id})" if c.parent_id else ""
        lines.append(f"  [{c.id}] {c.name} [{c.code or '-'}]{p}")
    return "\n".join(lines)


async def _tool_add_category(name, code, db):
    cat = Category(name=name, code=code)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return f"Added category #{cat.id}: {cat.name}"


async def _tool_delete_category(id, db):
    count = (await db.execute(
        select(sa_func.count(Book.id)).where(Book.category_id == id)
    )).scalar()
    if count:
        return f"Category #{id} has {count} books, cannot delete."
    cat = await db.get(Category, id)
    if not cat:
        return f"Category #{id} not found."
    name = cat.name
    await db.delete(cat)
    await db.commit()
    return f"Deleted category #{id}: {name}"


async def _tool_list_readers(db):
    result = await db.execute(select(Reader).order_by(Reader.id))
    readers = result.scalars().all()
    if not readers:
        return "No readers."
    lines = [f"Readers ({len(readers)}):"]
    for r in readers:
        lines.append(f"  [{r.id}] {r.name} (card: {r.card_number}, type: {r.identity_type or '-'})")
    return "\n".join(lines)


async def _tool_add_reader(data, db):
    existing = await db.execute(
        select(Reader).where(Reader.card_number == data.get("card_number", ""))
    )
    if existing.scalar_one_or_none():
        return f"Card '{data.get('card_number')}' already exists."
    reader = Reader(
        card_number=data.get("card_number", ""),
        name=data.get("name", ""),
        identity_type=data.get("identity_type"),
        phone=data.get("phone"),
        card_status="normal",
        max_borrow=data.get("max_borrow", 10),
        register_date=date.today(),
    )
    db.add(reader)
    await db.commit()
    await db.refresh(reader)
    return f"Added reader #{reader.id}: {reader.name}"


async def _tool_delete_reader(id, db):
    active = await db.execute(
        select(BorrowingRecord).where(
            BorrowingRecord.reader_id == id,
            BorrowingRecord.status == "借出"
        )
    )
    if active.scalar_one_or_none():
        return f"Reader #{id} has active borrows, cannot delete."
    r = await db.get(Reader, id)
    if not r:
        return f"Reader #{id} not found."
    name = r.name
    await db.delete(r)
    await db.commit()
    return f"Deleted reader #{id}: {name}"


async def _tool_get_reader(id, db):
    reader = await db.get(Reader, id)
    if not reader:
        return f"Reader #{id} not found."
    return (
        f"[{reader.id}] {reader.name}\n"
        f"  Card: {reader.card_number} | Type: {reader.identity_type or '-'}\n"
        f"  Phone: {reader.phone or '-'} | Status: {reader.card_status}\n"
        f"  Max Borrow: {reader.max_borrow} | Registered: {reader.register_date or '-'}"
    )


async def _tool_list_copies(book_id, db):
    result = await db.execute(
        select(BookCopy).where(BookCopy.book_id == book_id).order_by(BookCopy.id)
    )
    copies = result.scalars().all()
    if not copies:
        return f"No copies for book #{book_id}."
    lines = [f"Copies of book #{book_id} ({len(copies)}):"]
    for c in copies:
        lines.append(f"  ID:{c.id}  Asset:{c.asset_number or '-'}  Status:{c.status}  Shelf:{c.shelf or '-'}")
    return "\n".join(lines)


async def _tool_add_copy(data, db):
    book = await db.get(Book, data["book_id"])
    if not book:
        return f"Book #{data['book_id']} not found."
    count = (await db.execute(
        select(sa_func.count(BookCopy.id)).where(BookCopy.book_id == data["book_id"])
    )).scalar() or 0
    copy = BookCopy(
        book_id=data["book_id"],
        asset_number=f"{data['book_id']}-{count+1:03d}",
        status="在馆",
        shelf=data.get("shelf"),
    )
    db.add(copy)
    await db.commit()
    return f"Added copy #{copy.id} for book #{data['book_id']}"


async def _tool_borrow(data, db):
    reader = await db.get(Reader, data["reader_id"])
    if not reader:
        return f"Reader #{data['reader_id']} not found."
    copy = await db.get(BookCopy, data["copy_id"])
    if not copy:
        return f"Copy #{data['copy_id']} not found."
    if copy.status != "在馆":
        return f"Copy #{data['copy_id']} status is '{copy.status}', cannot borrow."
    book = await db.get(Book, copy.book_id)
    if book and (book.available_copies or 0) < 1:
        return f"Book '{book.title}' has no available copies."
    today = date.today()
    record = BorrowingRecord(
        reader_id=data["reader_id"],
        copy_id=data["copy_id"],
        borrow_date=today,
        due_date=today + timedelta(days=30),
        status="借出",
    )
    copy.status = "借出"
    if book:
        book.available_copies = (book.available_copies or 1) - 1
    db.add(record)
    await db.commit()
    return (f"Borrowed! Record #{record.id}, reader#{data['reader_id']} "
            f"borrowed copy#{data['copy_id']}, due: {record.due_date}")


async def _tool_return(data, db):
    result = await db.execute(
        select(BorrowingRecord).where(
            BorrowingRecord.copy_id == data["copy_id"],
            BorrowingRecord.status == "借出"
        ).order_by(BorrowingRecord.id.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return f"No active borrow for copy #{data['copy_id']}."
    today = date.today()
    overdue = max(0, (today - record.due_date).days) if record.due_date else 0
    record.return_date = today
    record.overdue_days = overdue
    record.status = "已归还"
    copy = await db.get(BookCopy, data["copy_id"])
    if copy:
        copy.status = "在馆"
        book = await db.get(Book, copy.book_id)
        if book:
            book.available_copies = (book.available_copies or 0) + 1
    await db.commit()
    msg = f"Returned copy #{data['copy_id']}"
    if overdue > 0:
        msg += f" (overdue {overdue} days)"
    return msg


async def _tool_renew_book(data, db):
    """Extend due_date for an active borrowing record."""
    copy_id = data["copy_id"]
    days = data.get("days", 30)
    
    result = await db.execute(
        select(BorrowingRecord).where(
            BorrowingRecord.copy_id == copy_id,
            BorrowingRecord.status == "借出"
        ).order_by(BorrowingRecord.id.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return f"No active borrow for copy #{copy_id}."
    
    current_due = record.due_date or date.today()
    new_due = current_due + timedelta(days=days)
    record.due_date = new_due
    await db.commit()
    
    return f"Renewed copy #{copy_id}, new due date: {new_due}"


async def _tool_list_borrowing(data, db):
    """List borrowing records with optional filters."""
    query = select(BorrowingRecord).order_by(BorrowingRecord.id.desc())
    
    reader_id = data.get("reader_id")
    status = data.get("status")
    
    if reader_id:
        query = query.where(BorrowingRecord.reader_id == reader_id)
    if status:
        query = query.where(BorrowingRecord.status == status)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    if not records:
        return "No borrowing records found."
    
    # Batch load related entities to avoid N+1 queries
    reader_ids = {r.reader_id for r in records}
    copy_ids = {r.copy_id for r in records}
    
    readers_result = await db.execute(select(Reader).where(Reader.id.in_(reader_ids)))
    readers_map = {r.id: r for r in readers_result.scalars().all()}
    
    copies_result = await db.execute(select(BookCopy).where(BookCopy.id.in_(copy_ids)))
    copies_map = {c.id: c for c in copies_result.scalars().all()}
    
    book_ids = {c.book_id for c in copies_map.values()}
    books_result = await db.execute(select(Book).where(Book.id.in_(book_ids)))
    books_map = {b.id: b for b in books_result.scalars().all()}
    
    lines = [f"Borrowing Records ({len(records)}):"]
    for r in records:
        reader = readers_map.get(r.reader_id)
        copy = copies_map.get(r.copy_id)
        book_name = ""
        if copy:
            book = books_map.get(copy.book_id)
            book_name = book.title if book else f"Book#{copy.book_id}"
        
        reader_name = reader.name if reader else f"Reader#{r.reader_id}"
        lines.append(
            f"  [{r.id}] {reader_name} borrowed '{book_name}'\n"
            f"      Copy#{r.copy_id} | Borrowed: {r.borrow_date or '-'} | "
            f"Due: {r.due_date or '-'} | Status: {r.status}"
        )
    return "\n".join(lines)


async def _tool_list_admins(db):
    result = await db.execute(select(Admin).order_by(Admin.id))
    admins = result.scalars().all()
    if not admins:
        return "No admins."
    lines = [f"Admins ({len(admins)}):"]
    for a in admins:
        lines.append(f"  [{a.id}] {a.username} ({a.name or '-'}) - {a.role}")
    return "\n".join(lines)


async def _tool_add_admin(data, db):
    existing = await db.execute(
        select(Admin).where(Admin.username == data.get("username", ""))
    )
    if existing.scalar_one_or_none():
        return f"Username '{data.get('username')}' already exists."
    admin = Admin(username=data.get("username", ""),
                  name=data.get("name"),
                  role=data.get("role", "admin"))
    admin.set_password(data.get("password", ""))
    db.add(admin)
    await db.commit()
    return f"Added admin #{admin.id}: {admin.username}"


async def _tool_count_statistics(group_by, db):
    total = (await db.execute(select(sa_func.count(Book.id)))).scalar() or 0
    readers = (await db.execute(select(sa_func.count(Reader.id)))).scalar() or 0
    borrowed = (await db.execute(
        select(sa_func.count(BorrowingRecord.id)).where(
            BorrowingRecord.status == "借出"
        )
    )).scalar() or 0
    lines = [f"Library Statistics",
             f"Total books: {total}",
             f"Total readers: {readers}",
             f"Currently borrowed: {borrowed}"]
    
    if group_by == "category":
        result = await db.execute(
            select(Category.name, sa_func.count(Book.id))
            .outerjoin(Book, Book.category_id == Category.id)
            .group_by(Category.id, Category.name)
            .order_by(sa_func.count(Book.id).desc())
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("By category:")
            for name, cnt in rows:
                lines.append(f"  {name}: {cnt}")
    elif group_by == "year":
        result = await db.execute(
            select(
                sa_func.strftime('%Y', Book.publication_date).label('year'),
                sa_func.count(Book.id)
            )
            .where(Book.publication_date.isnot(None))
            .group_by('year')
            .order_by('year')
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("By year:")
            for year, cnt in rows:
                lines.append(f"  {year}: {cnt}")
    elif group_by == "genre":
        result = await db.execute(
            select(Book.genre, sa_func.count(Book.id))
            .where(Book.genre.isnot(None))
            .group_by(Book.genre)
            .order_by(sa_func.count(Book.id).desc())
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("By genre:")
            for genre, cnt in rows:
                lines.append(f"  {genre}: {cnt}")
    elif group_by == "language":
        result = await db.execute(
            select(Book.language, sa_func.count(Book.id))
            .where(Book.language.isnot(None))
            .group_by(Book.language)
            .order_by(sa_func.count(Book.id).desc())
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("By language:")
            for lang, cnt in rows:
                lines.append(f"  {lang}: {cnt}")
    elif group_by == "status":
        result = await db.execute(
            select(BorrowingRecord.status, sa_func.count(BorrowingRecord.id))
            .group_by(BorrowingRecord.status)
            .order_by(sa_func.count(BorrowingRecord.id).desc())
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("By status:")
            for status, cnt in rows:
                lines.append(f"  {status}: {cnt}")
    elif group_by == "reader":
        result = await db.execute(
            select(Reader.name, sa_func.count(BorrowingRecord.id))
            .join(BorrowingRecord, BorrowingRecord.reader_id == Reader.id)
            .group_by(Reader.id, Reader.name)
            .order_by(sa_func.count(BorrowingRecord.id).desc())
            .limit(20)
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("Top readers:")
            for name, cnt in rows:
                lines.append(f"  {name}: {cnt}")
    elif group_by == "book":
        result = await db.execute(
            select(Book.title, sa_func.count(BorrowingRecord.id))
            .join(BookCopy, BorrowingRecord.copy_id == BookCopy.id)
            .join(Book, BookCopy.book_id == Book.id)
            .group_by(Book.id, Book.title)
            .order_by(sa_func.count(BorrowingRecord.id).desc())
            .limit(20)
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("Top books:")
            for title, cnt in rows:
                lines.append(f"  {title[:50]}: {cnt}")
    else:
        # Default: show category breakdown
        result = await db.execute(
            select(Category.name, sa_func.count(Book.id))
            .outerjoin(Book, Book.category_id == Category.id)
            .group_by(Category.id, Category.name)
            .order_by(sa_func.count(Book.id).desc())
            .limit(15)
        )
        rows = result.all()
        if rows:
            lines.append("")
            lines.append("By category (top 15):")
            for name, cnt in rows:
                lines.append(f"  {name}: {cnt}")
    
    return "\n".join(lines)


TOOL_DISPATCH = {
    "search_books": lambda a, d: _tool_search_books(a.get("query",""), a.get("limit",10), d),
    "get_book": lambda a, d: _tool_get_book(a["id"], d),
    "add_book": lambda a, d: _tool_add_book(a, d),
    "update_book": lambda a, d: _tool_update_book(a.pop("id"), a, d),
    "delete_book": lambda a, d: _tool_delete_book(a["id"], d),
    "list_categories": lambda a, d: _tool_list_categories(d),
    "add_category": lambda a, d: _tool_add_category(a["name"], a.get("code"), d),
    "delete_category": lambda a, d: _tool_delete_category(a["id"], d),
    "list_readers": lambda a, d: _tool_list_readers(d),
    "get_reader": lambda a, d: _tool_get_reader(a["id"], d),
    "add_reader": lambda a, d: _tool_add_reader(a, d),
    "delete_reader": lambda a, d: _tool_delete_reader(a["id"], d),
    "list_copies": lambda a, d: _tool_list_copies(a["book_id"], d),
    "add_copy": lambda a, d: _tool_add_copy(a, d),
    "list_borrowing": lambda a, d: _tool_list_borrowing(a, d),
    "borrow_book": lambda a, d: _tool_borrow(a, d),
    "return_book": lambda a, d: _tool_return(a, d),
    "renew_book": lambda a, d: _tool_renew_book(a, d),
    "list_admins": lambda a, d: _tool_list_admins(d),
    "add_admin": lambda a, d: _tool_add_admin(a, d),
    "count_statistics": lambda a, d: _tool_count_statistics(a.get("group_by","none"), d),
    "web_search": lambda a, d: _tool_web_search(a.get("query",""), d),
    "classify_book_info": lambda a, d: _classify_book_info(a, d),
    "classify_book": lambda a, d: _classify_book_info(a, d),
}


def _extract_json(text):
    try:
        start = text.index("{")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1])
    except (ValueError, json.JSONDecodeError):
        pass
    return None


async def _tool_web_search(query, db):
    """Search the web for information."""
    return await web_search(query, max_results=5)


async def _classify_book_info(data, db):
    """Classify a book using LLM + web search for accurate categorization."""
    title = data.get("title", "")
    authors = data.get("authors", "")
    cat_ctx = await _get_categories_context(db)

    # Step 1: Search the web for book info
    web_info = await search_book_info(title, authors)

    # Step 2: Use LLM to classify based on web info + local categories
    prompt = f"""You are a professional librarian. Classify this book into the best matching category.

Available categories in the library:
{cat_ctx}

Book to classify:
- Title: {title}
- Authors: {authors}

Web search results about this book:
{web_info}

Analyze the web search results to understand the book's subject, genre, and academic field.
Then match it to the most appropriate category from the library's category list.

Output ONLY JSON:
{{"category_id": <id or null if no match>, "category_name": "<matched or suggested name>",
  "call_number": "<suggested call number based on category>", "language": "<guessed language: zh/en/etc>",
  "confidence": "<high/medium/low>", "reason": "<brief reason for classification>"}}"""

    model = await db.get(LLMModel, 1)
    if not model:
        return "Please configure an LLM model first."
    client = LLMClient(
        provider=model.provider, api_base=model.api_base,
        api_key=model.api_key or "",
        model_name=model.model_name, temperature=0.1, max_tokens=1024,
    )
    try:
        resp = await client.chat_completion([
            {"role": "system", "content": "You are a professional librarian. Output only JSON."},
            {"role": "user", "content": prompt},
        ])
        reply = resp["choices"][0]["message"]["content"].strip()
        obj = _extract_json(reply)
        return json.dumps(obj, ensure_ascii=False) if obj else reply
    except Exception as e:
        return f"Classification failed: {e}"


class DBAgent:
    """Natural language database agent - keyword dispatch with LLM fallback."""

    def __init__(self, model_id: int, db: AsyncSession):
        self.model_id = model_id
        self.db = db

    async def execute(self, instruction: str) -> str:
        # Try keyword-based dispatch first (fast and reliable)
        result = await self._keyword_dispatch(instruction)
        if result is not None:
            return result

        # Fall back to LLM for complex queries
        return await self._llm_dispatch(instruction)

    async def _keyword_dispatch(self, instruction: str) -> Optional[str]:
        """Simple keyword-based tool dispatch with fuzzy matching."""
        text = instruction.lower().strip()

        # Statistics - broad fuzzy matching
        if any(kw in text for kw in [
            "统计", "statistics", "总数", "多少本", "多少读者", "一共", "有多少",
            "概览", "概况", "汇总", "overview", "summary", "总共有",
            "多少书", "几个读者", "几本书", "多少个",
        ]):
            fn = TOOL_DISPATCH.get("count_statistics")
            if fn:
                return await fn({"group_by": "category"}, self.db)

        # Readers - broad fuzzy matching
        if any(kw in text for kw in [
            "列出读者", "所有读者", "读者列表", "查看读者", "读者管理", "列出所有读者",
            "读者", "reader", "有哪些读者", "看看读者", "读者信息", "谁借了书",
            "会员", "借阅者",
        ]):
            fn = TOOL_DISPATCH.get("list_readers")
            if fn:
                return await fn({}, self.db)

        # Books - broad fuzzy matching
        if any(kw in text for kw in [
            "列出图书", "所有图书", "图书列表", "查看图书", "显示图书", "列出所有图书", "图书管理",
            "列出书籍", "书籍列表", "所有书籍", "看看书", "有什么书",
            "book", "books", "图书馆有什么", "馆藏", "书架",
        ]):
            fn = TOOL_DISPATCH.get("search_books")
            if fn:
                return await fn({"query": "", "limit": 100}, self.db)

        # Borrowing - broad fuzzy matching
        if any(kw in text for kw in [
            "借阅", "borrow", "还书", "借书", "借阅记录", "借阅管理",
            "谁借了", "借出", "归还", "逾期", "overdue", "借还",
        ]):
            fn = TOOL_DISPATCH.get("list_borrowing")
            if fn:
                return await fn({}, self.db)

        # Categories - broad fuzzy matching
        if any(kw in text for kw in [
            "分类", "category", "类别", "图书分类", "分类管理",
            "有哪些分类", "分类列表", "book category",
        ]):
            fn = TOOL_DISPATCH.get("list_categories")
            if fn:
                return await fn({}, self.db)

        # Search books with query - extract search terms
        search_kw = ["搜索", "search", "查找", "找书", "查询", "找", "搜"]
        if any(kw in text for kw in search_kw):
            fn = TOOL_DISPATCH.get("search_books")
            if fn:
                query = instruction
                for kw in search_kw:
                    query = query.replace(kw, "")
                query = query.strip().rstrip("。.!！，,")
                if not query:
                    query = ""
                return await fn({"query": query, "limit": 10}, self.db)

        # Web search for book info
        if any(kw in text for kw in ["联网搜索", "网上查", "搜索这本书", "查找这本书的信息", "web search", "查一下这本书"]):
            fn = TOOL_DISPATCH.get("web_search")
            if fn:
                query = instruction
                for kw in ["联网搜索", "网上查", "搜索这本书", "查找这本书的信息", "web search", "查一下这本书"]:
                    query = query.replace(kw, "")
                query = query.strip().rstrip("。.!！")
                if not query:
                    query = instruction
                return await fn({"query": query + " book category genre"}, self.db)

        # Classify book with web search
        if any(kw in text for kw in ["分类这本书", "帮我分类", "classify", "这本书属于", "给这本书分类", "智能分类"]):
            fn = TOOL_DISPATCH.get("classify_book")
            if fn:
                query = instruction
                for kw in ["分类这本书", "帮我分类", "classify", "这本书属于", "给这本书分类", "智能分类", "：", ":"]:
                    query = query.replace(kw, "")
                query = query.strip()
                parts = query.split()
                title = parts[0] if parts else query
                authors = " ".join(parts[1:]) if len(parts) > 1 else ""
                return await fn({"title": title, "authors": authors}, self.db)

        return None  # No keyword match, use LLM

    async def _llm_dispatch(self, instruction: str) -> str:
        """Use LLM for complex queries or natural conversation."""
        model = await self.db.get(LLMModel, self.model_id)
        if not model:
            return f"[Error] Model #{self.model_id} not found."

        client = LLMClient(
            provider=model.provider, api_base=model.api_base,
            api_key=model.api_key or "",
            model_name=model.model_name, temperature=0.7, max_tokens=2048,
        )

        cat_ctx = await _get_categories_context(self.db)
        sys_prompt = TOOL_SYSTEM_PROMPT + f"\n\nCurrent database:\n{cat_ctx}"

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": instruction},
        ]

        # Try up to 3 times to get valid JSON
        call = None
        reply = ""
        for attempt in range(3):
            try:
                data = await client.chat_completion(messages)
                reply = data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                return f"[AI connection error] {e}"

            call = _extract_json(reply)
            if call is not None and "tool" in call:
                break

            # Retry with stronger instruction
            messages.append({"role": "assistant", "content": reply})
            if attempt == 0:
                messages.append({
                    "role": "user",
                    "content": "You did not output valid JSON. You MUST respond with ONLY a JSON object like: {\"tool\": \"tool_name\", \"args\": {...}}. Do not include any other text."
                })
            else:
                messages.append({
                    "role": "user",
                    "content": "STRICT: Output ONLY the JSON. Example: {\"tool\": \"list_readers\", \"args\": {}}"
                })

        if call is None or "tool" not in call:
            # Not a tool call - return the LLM's natural language response directly
            # This allows normal conversation (greetings, chitchat, etc.)
            return reply

        tool_name = call.get("tool")
        args = call.get("args", {})
        fn = TOOL_DISPATCH.get(tool_name)
        if not fn:
            return f"Unknown tool '{tool_name}'."

        try:
            result = await fn(args, self.db)
        except Exception as e:
            result = f"[Execution error] {e}"

        return result
