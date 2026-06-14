# -*- coding: utf-8 -*-
"""Constants and enumerations for the library management system."""

from enum import Enum


class BookStatus(str, Enum):
    """Book availability status."""
    AVAILABLE = "在馆"
    BORROWED = "借出"
    RESERVED = "预约"
    LOST = "遗失"
    DAMAGED = "损坏"


class BorrowingStatus(str, Enum):
    """Borrowing record status."""
    ACTIVE = "借出"
    RETURNED = "已归还"
    OVERDUE = "逾期"
    PENDING_CONFIRM = "待确认"


class ReaderCardStatus(str, Enum):
    """Reader card status."""
    NORMAL = "正常"
    LOST = "挂失"
    CANCELLED = "注销"


class AdminRole(str, Enum):
    """Admin role types."""
    SUPER_ADMIN = "超级管理员"
    ADMIN = "普通管理员"
    ASSISTANT = "助理管理员"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    OLLAMA = "ollama"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    TOGETHER = "together"
    MISTRAL = "mistral"
    OPENROUTER = "openrouter"
    GITHUB = "github"
    OTHER = "other"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


# Default values
DEFAULT_BORROW_DAYS = 30
DEFAULT_MAX_BORROW = 10
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File upload
ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "image/bmp",
}

ALLOWED_EXCEL_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
}

# Rate limiting
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_BURST = 10

# Cache TTL (seconds)
CACHE_TTL_CATEGORIES = 300
CACHE_TTL_MODELS = 60
