from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LLMModelBase(BaseModel):
    name: str = Field(..., max_length=128)
    provider: str = Field(..., max_length=64)
    model_name: str = Field(..., max_length=128)
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    is_active: bool = True
    sort_order: int = 0


class LLMModelCreate(LLMModelBase):
    pass


class LLMModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class LLMModelResponse(LLMModelBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    code: Optional[str] = None
    name: str = Field(..., max_length=128)
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    code: Optional[str] = None
    name: str
    parent_id: Optional[int] = None
    children: list = []
    class Config:
        from_attributes = True


class BookBase(BaseModel):
    call_number: Optional[str] = None
    title: str = Field(..., max_length=512)
    subtitle: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    edition: Optional[str] = None
    isbn: Optional[str] = None
    category_id: Optional[int] = None
    language: Optional[str] = None
    pages: Optional[int] = None
    price: Optional[float] = None
    location: Optional[str] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    call_number: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    edition: Optional[str] = None
    isbn: Optional[str] = None
    category_id: Optional[int] = None
    language: Optional[str] = None
    pages: Optional[int] = None
    price: Optional[float] = None
    location: Optional[str] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class BookResponse(BaseModel):
    id: int
    call_number: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    edition: Optional[str] = None
    isbn: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    language: Optional[str] = None
    pages: Optional[int] = None
    price: Optional[float] = None
    location: Optional[str] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    items: list[BookResponse]
    total: int


class BookCopyResponse(BaseModel):
    id: int
    book_id: int
    asset_number: Optional[str] = None
    entry_date: Optional[str] = None
    status: Optional[str] = None
    shelf: Optional[str] = None
    class Config:
        from_attributes = True


class ReaderCreate(BaseModel):
    card_number: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    identity_type: Optional[str] = None
    phone: Optional[str] = None
    register_date: Optional[str] = None
    card_status: Optional[str] = None
    max_borrow: Optional[int] = None


class ReaderUpdate(BaseModel):
    name: Optional[str] = None
    identity_type: Optional[str] = None
    phone: Optional[str] = None
    card_status: Optional[str] = None
    max_borrow: Optional[int] = None


class AdminCreate(BaseModel):
    username: str = Field(..., max_length=64)
    password: str = Field(..., max_length=256)
    name: Optional[str] = None
    role: Optional[str] = None


class BorrowingResponse(BaseModel):
    id: int
    reader_id: int
    copy_id: int
    borrow_date: Optional[str] = None
    due_date: Optional[str] = None
    return_date: Optional[str] = None
    overdue_days: Optional[int] = None
    admin_id: Optional[int] = None
    status: Optional[str] = None
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str = "New conversation"
    model_id: Optional[int] = None
    system_prompt: Optional[str] = None
    context_book_ids: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    messages: list[MessageResponse] = []
    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    id: int
    book_id: int
    filename: str
    filepath: str
    file_size: int = 0
    mime_type: Optional[str] = None
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    model_id: int
    message: str
    system_prompt: Optional[str] = None
    book_context_ids: Optional[list[int]] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    tokens_in: int
    tokens_out: int
