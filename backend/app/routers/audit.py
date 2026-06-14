# -*- coding: utf-8 -*-
"""Audit log router. Provides endpoints for querying audit logs."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import AuditLog

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs")
async def list_audit_logs(
    user_type: Optional[str] = Query(None, description="用户类型: admin 或 reader"),
    action: Optional[str] = Query(None, description="操作类型: create, update, delete, login 等"),
    resource_type: Optional[str] = Query(None, description="资源类型: book, reader, borrowing 等"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with pagination and filters."""
    query = select(AuditLog)
    count_query = select(sa_func.count()).select_from(AuditLog)

    # Apply filters
    if user_type:
        query = query.where(AuditLog.user_type == user_type)
        count_query = count_query.where(AuditLog.user_type == user_type)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(AuditLog.created_at >= start_dt)
            count_query = count_query.where(AuditLog.created_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            # Include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.where(AuditLog.created_at <= end_dt)
            count_query = count_query.where(AuditLog.created_at <= end_dt)
        except ValueError:
            pass

    # Get total count
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_type": log.user_type,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": str(log.created_at) if log.created_at else "",
        })

    return {"data": data, "total": total}
