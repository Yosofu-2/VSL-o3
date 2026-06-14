"""Test admin login flow."""
import asyncio
from app.database import async_session, engine
from app.models.model import Admin, Base
from sqlalchemy import select

async def test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        r = await db.execute(select(Admin).where(Admin.username == 'admin'))
        admin = r.scalar_one_or_none()
        if not admin:
            print("Admin not found!")
            return
        
        print(f"Admin: {admin.name}")
        print(f"Password hash: {admin.password}")
        
        ok = admin.check_password("admin123")
        print(f"Password OK: {ok}")

asyncio.run(test())
