"""System management endpoints for database backup and restore."""

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/api/system", tags=["system"])

BACKUP_DIR = Path(__file__).parent.parent.parent / "backups"


@router.get("/backups")
async def list_backups():
    """List all database backups."""
    BACKUP_DIR.mkdir(exist_ok=True)
    files = sorted(BACKUP_DIR.glob("*.db"), reverse=True)
    return {
        "data": [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
            for f in files
        ],
        "total": len(files),
    }


@router.post("/backup")
async def create_backup(db: AsyncSession = Depends(get_db)):
    """Create a database backup."""
    BACKUP_DIR.mkdir(exist_ok=True)
    db_path = Path(
        settings.database_url
        .replace("sqlite+aiosqlite:///", "")
        .replace("sqlite:///", "")
    )
    if not db_path.exists():
        raise HTTPException(404, "数据库文件不存在")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(db_path, backup_path)
    return {
        "message": "备份成功",
        "filename": backup_name,
        "size": backup_path.stat().st_size,
    }


@router.post("/restore/{filename}")
async def restore_backup(filename: str, db: AsyncSession = Depends(get_db)):
    """Restore database from backup."""
    backup_path = BACKUP_DIR / filename
    if not backup_path.exists():
        raise HTTPException(404, "备份文件不存在")
    db_path = Path(
        settings.database_url
        .replace("sqlite+aiosqlite:///", "")
        .replace("sqlite:///", "")
    )
    shutil.copy2(backup_path, db_path)
    return {"message": "恢复成功", "filename": filename}


@router.delete("/backups/{filename}")
async def delete_backup(filename: str):
    """Delete a backup file."""
    backup_path = BACKUP_DIR / filename
    if not backup_path.exists():
        raise HTTPException(404, "备份文件不存在")
    backup_path.unlink()
    return {"message": "删除成功"}
