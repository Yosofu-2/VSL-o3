"""
LitManager data models -- clean English column names, password hashing, proper cascades.
"""

import hashlib
import secrets

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.security import hash_password as _hash_pw
from app.security import verify_password as _verify_pw


def hash_password(password: str) -> str:
    """Hash password using bcrypt from security module."""
    return _hash_pw(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify password with backward compatibility for SHA256 format.

    Tries bcrypt first (new format, starts with '$2'), then falls back to
    old SHA256 format (contains ':' separator).
    """
    # Try bcrypt first (new format)
    if hashed and hashed.startswith("$2"):
        return _verify_pw(password, hashed)

    # Try old SHA256 format (salt:hash)
    if ":" in hashed:
        try:
            salt, h = hashed.split(":", 1)
            if h == hashlib.sha256((salt + password).encode()).hexdigest():
                return True
        except (ValueError, AttributeError):
            pass

    return False


class LLMModel(Base):
    __tablename__ = "llm_models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(128), nullable=False)
    provider = Column("provider", String(64), nullable=False)
    model_name = Column("model_name", String(128), nullable=False)
    api_base = Column("api_base", String(512))
    api_key = Column("api_key", String(512))
    temperature = Column("temperature", Float, default=0.7)
    max_tokens = Column("max_tokens", Integer, default=4096)
    is_active = Column("is_active", Integer, default=1)
    sort_order = Column("sort_order", Integer, default=0)
    created_at = Column("created_at", DateTime, server_default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())
    conversations = relationship("Conversation", back_populates="model")
    def __repr__(self):
        return f"<LLMModel {self.id}: {self.name} ({self.provider}/{self.model_name})>"


class Category(Base):
    __tablename__ = "book_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(64))
    name = Column("name", String(128), nullable=False)
    parent_id = Column("parent_id", Integer, ForeignKey("book_categories.id"))
    children = relationship("Category", backref="parent", remote_side=[id])
    books = relationship("Book", back_populates="category")
    def __repr__(self):
        return f"<Category {self.id}: {self.name}>"


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_number = Column("call_number", String(64))
    title = Column("title", String(512), nullable=False, index=True)
    subtitle = Column("subtitle", String(512))
    authors = Column("authors", Text)
    publisher = Column("publisher", String(256))
    publication_year = Column("publication_year", Integer)
    edition = Column("edition", String(64))
    isbn = Column("isbn", String(32))
    category_id = Column("category_id", Integer, ForeignKey("book_categories.id"))
    language = Column("language", String(32))
    pages = Column("pages", Integer)
    price = Column("price", Float)
    location = Column("location", String(256))
    total_copies = Column("total_copies", Integer, default=0)
    available_copies = Column("available_copies", Integer, default=0)
    status = Column("status", String(32), default="在馆")
    created_at = Column("created_at", DateTime, server_default=func.now())
    notes = Column("notes", Text)
    category = relationship("Category", back_populates="books")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="book", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Book {self.id}: {self.title}>"


class BookCopy(Base):
    __tablename__ = "book_copies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column("book_id", Integer, ForeignKey("books.id"), nullable=False)
    asset_number = Column("asset_number", String(64), unique=True)
    entry_date = Column("entry_date", Date)
    status = Column("status", String(32), default="在馆")
    shelf = Column("shelf", String(128))
    book = relationship("Book", back_populates="copies")
    borrowing_records = relationship("BorrowingRecord", back_populates="copy", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<BookCopy {self.id}: {self.asset_number} ({self.status})>"


class Reader(Base):
    __tablename__ = "readers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_number = Column("card_number", String(64), unique=True, nullable=False)
    name = Column("name", String(128), nullable=False)
    identity_type = Column("identity_type", String(32))
    phone = Column("phone", String(32))
    register_date = Column("register_date", Date)
    card_status = Column("card_status", String(16), default="正常")
    max_borrow = Column("max_borrow", Integer, default=10)
    password = Column("password", String(256))  # 读者登录密码
    borrowing_records = relationship("BorrowingRecord", back_populates="reader", cascade="all, delete-orphan")
    
    def set_password(self, raw: str):
        self.password = hash_password(raw)

    def check_password(self, raw: str) -> bool:
        result = verify_password(raw, self.password)
        # If password verified with old SHA256 format, re-hash with bcrypt
        if result and self.password and ":" in self.password and not self.password.startswith("$2"):
            self.password = hash_password(raw)
        return result
    
    def __repr__(self):
        return f"<Reader {self.id}: {self.name}>"


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column("username", String(64), unique=True, nullable=False)
    password = Column("password", String(256), nullable=False)
    name = Column("name", String(128))
    role = Column("role", String(32), default="普通管理员")
    join_date = Column("join_date", Date)
    borrowing_records = relationship("BorrowingRecord", back_populates="operator_admin", cascade="all, delete-orphan")
    def set_password(self, raw: str):
        self.password = hash_password(raw)
    def check_password(self, raw: str) -> bool:
        result = verify_password(raw, self.password)
        # If password verified with old SHA256 format, re-hash with bcrypt
        if result and self.password and ":" in self.password and not self.password.startswith("$2"):
            self.password = hash_password(raw)
        return result
    def __repr__(self):
        return f"<Admin {self.id}: {self.username}>"


class BorrowingRecord(Base):
    __tablename__ = "borrowing_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reader_id = Column("reader_id", Integer, ForeignKey("readers.id"), nullable=False)
    copy_id = Column("copy_id", Integer, ForeignKey("book_copies.id"), nullable=False)
    borrow_date = Column("borrow_date", Date)
    due_date = Column("due_date", Date)
    return_date = Column("return_date", Date, nullable=True)
    overdue_days = Column("overdue_days", Integer, default=0)
    admin_id = Column("admin_id", Integer, ForeignKey("admins.id"))
    status = Column("status", String(16), default="借出")
    renewed = Column("renewed", Integer, default=0)  # 0=no, 1=yes
    reader = relationship("Reader", back_populates="borrowing_records")
    copy = relationship("BookCopy", back_populates="borrowing_records")
    operator_admin = relationship("Admin", back_populates="borrowing_records")
    def __repr__(self):
        return f"<BorrowingRecord {self.id}: copy#{self.copy_id} -> reader#{self.reader_id} ({self.status})>"


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column("book_id", Integer, ForeignKey("books.id"), nullable=False)
    filename = Column("filename", String(256), nullable=False)
    filepath = Column("filepath", String(512), nullable=False)
    file_size = Column("file_size", Integer, default=0)
    mime_type = Column("mime_type", String(64))
    created_at = Column("created_at", DateTime, server_default=func.now())
    book = relationship("Book", back_populates="attachments")
    def __repr__(self):
        return f"<Attachment {self.id}: {self.filename}>"


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column("title", String(256), default="New conversation")
    model_id = Column("model_id", Integer, ForeignKey("llm_models.id"))
    system_prompt = Column("system_prompt", Text)
    context_book_ids = Column("context_book_ids", Text, comment="JSON array of book IDs")
    created_at = Column("created_at", DateTime, server_default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())
    model = relationship("LLMModel", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Conversation {self.id}: {self.title}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("user_id", Integer, nullable=True)
    user_type = Column("user_type", String(16))
    action = Column("action", String(32), nullable=False)
    resource_type = Column("resource_type", String(32), nullable=False)
    resource_id = Column("resource_id", Integer, nullable=True)
    details = Column("details", Text)
    ip_address = Column("ip_address", String(64))
    created_at = Column("created_at", DateTime, server_default=func.now())

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.user_type}#{self.user_id} {self.action} {self.resource_type}#{self.resource_id}>"


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column("conversation_id", Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column("role", String(16), nullable=False)
    content = Column("content", Text, nullable=False)
    tokens_in = Column("tokens_in", Integer, default=0)
    tokens_out = Column("tokens_out", Integer, default=0)
    created_at = Column("created_at", DateTime, server_default=func.now())
    conversation = relationship("Conversation", back_populates="messages")
    def __repr__(self):
        return f"<Message {self.id}: {self.role}>"


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reader_id = Column("reader_id", Integer, ForeignKey("readers.id"), nullable=False)
    book_id = Column("book_id", Integer, ForeignKey("books.id"), nullable=False)
    status = Column("status", String(16), default="等待中")  # 等待中/已通知/已取消/已借阅
    created_at = Column("created_at", DateTime, server_default=func.now())
    notified_at = Column("notified_at", DateTime)
    reader = relationship("Reader")
    book = relationship("Book")
    def __repr__(self):
        return f"<Reservation {self.id}: reader#{self.reader_id} book#{self.book_id} ({self.status})>"


class Fine(Base):
    __tablename__ = "fines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reader_id = Column("reader_id", Integer, ForeignKey("readers.id"), nullable=False)
    borrowing_id = Column("borrowing_id", Integer, ForeignKey("borrowing_records.id"))
    amount = Column("amount", Float, nullable=False)
    reason = Column("reason", String(256))
    is_paid = Column("is_paid", Integer, default=0)
    created_at = Column("created_at", DateTime, server_default=func.now())
    reader = relationship("Reader")
    def __repr__(self):
        return f"<Fine {self.id}: reader#{self.reader_id} amount={self.amount}>"


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("user_id", Integer, nullable=False)  # reader or admin id
    user_type = Column("user_type", String(16), nullable=False)  # "reader" or "admin"
    type = Column("type", String(32), nullable=False)  # "overdue", "reservation_ready", "return_confirmed", "return_rejected", "system"
    title = Column("title", String(256), nullable=False)
    content = Column("content", Text)
    is_read = Column("is_read", Integer, default=0)  # 0=unread, 1=read
    related_id = Column("related_id", Integer)  # related borrowing/record id
    created_at = Column("created_at", DateTime, server_default=func.now())
    read_at = Column("read_at", DateTime)
    def __repr__(self):
        return f"<Notification {self.id}: {self.type} for {self.user_type}#{self.user_id}>"
