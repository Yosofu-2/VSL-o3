"""Admin router. English keys, password hashing."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import Admin
from app.utils import log_audit
from app.security import create_access_token, get_current_admin

router = APIRouter(prefix="/api/admins", tags=["admins"])


class AdminCreateBody(BaseModel):
    username: str
    password: str
    name: str | None = None
    role: str | None = "普通管理员"


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(body: LoginBody, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate admin credentials. Returns admin info with JWT token on success."""
    result = await db.execute(select(Admin).where(Admin.username == body.username))
    admin = result.scalar_one_or_none()

    if not admin or not admin.check_password(body.password):
        raise HTTPException(401, "用户名或密码错误")

    # Generate JWT token
    token = create_access_token(
        data={
            "sub": str(admin.id),
            "username": admin.username,
            "role": admin.role,
            "type": "admin"
        }
    )

    # Log audit
    await log_audit(
        db=db,
        user_id=admin.id,
        user_type="admin",
        action="login",
        resource_type="admin",
        resource_id=admin.id,
        details={"username": admin.username},
        ip_address=request.client.host if request.client else None
    )

    return {
        "token": token,
        "id": admin.id,
        "username": admin.username,
        "name": admin.name or admin.username,
        "role": admin.role,
        "join_date": str(admin.join_date) if admin.join_date else "",
    }


@router.get("/")
async def list_admins(
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    result = await db.execute(select(Admin).order_by(Admin.id))
    rows = result.scalars().all()
    return {"data": [{"id": r.id, "username": r.username, "name": r.name,
                       "role": r.role, "join_date": str(r.join_date) if r.join_date else ""} for r in rows],
            "total": len(rows)}


@router.post("/")
async def create_admin(body: AdminCreateBody, request: Request, db: AsyncSession = Depends(get_db), current_admin: dict = Depends(get_current_admin)):
    exists = await db.execute(select(Admin).where(Admin.username == body.username))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "账号已存在")
    admin = Admin(
        username=body.username,
        name=body.name,
        role=body.role or "普通管理员",
        join_date=datetime.date.today(),
    )
    admin.set_password(body.password)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    # Log audit
    await log_audit(
        db=db,
        user_id=admin.id,
        user_type="admin",
        action="create",
        resource_type="admin",
        resource_id=admin.id,
        details={"username": admin.username, "name": admin.name, "role": admin.role},
        ip_address=request.client.host if request.client else None
    )

    return {"id": admin.id, "message": "添加成功"}
