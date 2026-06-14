"""Full login flow test."""
import asyncio
from app.database import async_session, engine
from app.models.model import Reader, Base
from sqlalchemy import select

async def test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        r = await db.execute(select(Reader).where(Reader.card_number == 'R001'))
        reader = r.scalar_one_or_none()
        print(f"Reader found: {reader is not None}")
        print(f"Password: {reader.password}")
        print(f"Password type: {type(reader.password)}")
        
        # Test check_password
        try:
            result = reader.check_password("reader123")
            print(f"check_password result: {result}")
        except Exception as e:
            print(f"check_password ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(test())
