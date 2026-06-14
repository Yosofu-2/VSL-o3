from pydantic_settings import BaseSettings
from typing import List
import secrets
import os
import sys
from pathlib import Path


def _get_base_dir() -> Path:
    """Get the base directory, handling both development and PyInstaller frozen modes."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: use the directory containing the executable
        return Path(sys.executable).parent
    else:
        # Development: use project root
        return Path(__file__).parent.parent.parent


def _get_data_dir() -> Path:
    """Get the data directory for database and key files."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: use 'data' subdirectory next to executable
        data_dir = Path(sys.executable).parent / "data"
    else:
        # Development: use project root
        data_dir = Path(__file__).parent.parent.parent
    data_dir.mkdir(exist_ok=True)
    return data_dir


def _load_or_create_key(env_var: str, filename: str) -> str:
    """从环境变量或文件加载密钥，如果都不存在则生成并保存"""
    # 1. 先尝试环境变量
    env_value = os.environ.get(env_var)
    if env_value:
        return env_value

    # 2. 尝试从文件读取（数据目录）
    data_dir = _get_data_dir()
    key_file = data_dir / filename

    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    # 3. 生成新密钥并保存到文件
    new_key = secrets.token_urlsafe(32)
    key_file.write_text(new_key, encoding="utf-8")
    return new_key


class Settings(BaseSettings):
    # Application
    app_name: str = "LitManager Library Management System"
    app_version: str = "2.0.0"
    debug: bool = False

    # Database
    database_url: str = f"sqlite+aiosqlite:///{_get_data_dir() / 'llm_manager.db'}"

    # Security - JWT Authentication
    secret_key: str = _load_or_create_key("SECRET_KEY", ".secret_key")
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Security - API Key Encryption
    api_key_encryption_key: str = _load_or_create_key("API_KEY_ENCRYPTION_KEY", ".api_key_encryption_key")

    # Security - CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["Authorization", "Content-Type"]

    # Database Connection Pool
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


settings = Settings()
