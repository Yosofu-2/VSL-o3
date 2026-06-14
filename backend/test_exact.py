"""Simulate exact login flow."""
import asyncio
from app.database import async_session, engine
from app.models.model import Reader, Base
from app.security import create_access_token
from sqlalchemy import select

async def test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        r = await db.execute(select(Reader).where(Reader.card_number == 'R001'))
        reader = r.scalar_one_or_none()
        if not reader:
            print("NOT FOUND")
            return
        
        print(f"Reader: {reader.name}")
        print(f"Has password: {bool(reader.password)}")
        
        # Step 1: check_password
        ok = reader.check_password("reader123")
        print(f"Password OK: {ok}")
        
        if not ok:
            print("FAIL: password wrong")
            return
        
        # Step 2: commit (password migration)
        await db.commit()
        print("Commit OK")
        
        # Step 3: check status
        print(f"Card status: {reader.card_status}")
        
        # Step 4: create token
        token = create_access_token(data={
            "sub": str(reader.id),
            "card_number": reader.card_number,
            "role": "reader",
            "type": "reader"
        })
        print(f"Token: {token[:30]}...")
        print("SUCCESS")

asyncio.run(test())
