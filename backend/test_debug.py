"""Full debug of reader login."""
import asyncio
import traceback
from app.database import async_session, engine
from app.models.model import Reader, Base
from sqlalchemy import select

async def debug():
    # Create tables if needed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        r = await db.execute(select(Reader).where(Reader.card_number == 'R001'))
        reader = r.scalar_one_or_none()
        if not reader:
            print("Reader R001 not found!")
            return
        
        print(f"Reader: {reader.name}, password set: {bool(reader.password)}")
        
        # Test check_password
        try:
            result = reader.check_password("reader123")
            print(f"check_password result: {result}")
        except Exception as e:
            print(f"check_password ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()
        
        # Test commit
        try:
            await db.commit()
            print("db.commit() OK")
        except Exception as e:
            print(f"db.commit() ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()

asyncio.run(debug())
