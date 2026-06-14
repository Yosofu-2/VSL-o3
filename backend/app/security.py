# -*- coding: utf-8 -*-
"""Security utilities for authentication, authorization, and encryption."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from cryptography.fernet import Fernet
import base64

from app.config import settings

# JWT configuration
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# API key encryption
API_KEY_ENCRYPTION_KEY = settings.api_key_encryption_key

# Password hashing using bcrypt directly (passlib is incompatible with bcrypt 4.x)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, AttributeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing token payload data
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for secure storage.

    Args:
        api_key: Plain text API key

    Returns:
        Encrypted API key string (base64 encoded)
    """
    if not api_key:
        return ""

    f = Fernet(API_KEY_ENCRYPTION_KEY)
    encrypted = f.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key from storage.

    Args:
        encrypted_key: Encrypted API key string (base64 encoded)

    Returns:
        Decrypted plain text API key
    """
    if not encrypted_key:
        return ""

    try:
        f = Fernet(API_KEY_ENCRYPTION_KEY)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception:
        # If decryption fails, return empty string
        # This handles legacy unencrypted keys gracefully
        return ""


# HTTP Bearer token scheme
security_scheme = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    """Dependency to extract and validate the current admin user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        Dictionary containing admin user information (id, username, role)

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    token_type = payload.get("type")

    if admin_id is None or username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure this is an admin token
    if token_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return {"id": int(admin_id), "username": username, "role": role, "type": token_type}


async def get_current_reader(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    """Dependency to extract and validate the current reader from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        Dictionary containing reader information (id, card_number, role)

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    reader_id = payload.get("sub")
    card_number = payload.get("card_number")
    role = payload.get("role")
    token_type = payload.get("type")

    if reader_id is None or card_number is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure this is a reader token
    if token_type != "reader":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reader access required",
        )

    return {"id": int(reader_id), "card_number": card_number, "role": role, "type": token_type}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    """Dependency to extract and validate the current user (admin or reader) from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        Dictionary containing user information (id, role, type, and additional fields)

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    token_type = payload.get("type")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return user info based on token type
    if token_type == "admin":
        return {
            "id": int(user_id),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "type": token_type
        }
    elif token_type == "reader":
        return {
            "id": int(user_id),
            "card_number": payload.get("card_number"),
            "role": payload.get("role"),
            "type": token_type
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str):
    """Dependency factory to check if current user has required role.

    Args:
        required_role: Required role level (e.g., "admin", "super_admin")

    Returns:
        Dependency function that checks role permission

    Raises:
        HTTPException: If user doesn't have required role
    """

    async def role_checker(current_admin: dict = Depends(get_current_admin)) -> dict:
        user_role = current_admin.get("role", "")

        # Role hierarchy: super_admin > admin > assistant
        role_hierarchy = {
            "super_admin": 3,
            "admin": 2,
            "assistant": 1,
            "普通管理员": 2,
            "超级管理员": 3,
            "助理管理员": 1,
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return current_admin

    return role_checker


def generate_api_key() -> str:
    """Generate a secure random API key.

    Returns:
        Random 32-byte API key encoded as hex string
    """
    return secrets.token_hex(32)


def generate_password_reset_token() -> str:
    """Generate a secure password reset token.

    Returns:
        Random 32-byte token encoded as URL-safe base64
    """
    return secrets.token_urlsafe(32)
