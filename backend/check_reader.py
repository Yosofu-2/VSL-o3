"""Check reader password hash format."""
import asyncio
from app.database import async_session
from app.models.model import Reader
from sqlalchemy import select

async def check():
    async with async_session() as db:
        r = await db.execute(select(Reader).where(Reader.card_number == 'R001'))
        reader = r.scalar_one_or_none()
        if reader:
            print(f'ID: {reader.id}')
            print(f'Name: {reader.name}')
            print(f'Password hash: {reader.password}')
            if reader.password:
                print(f'Starts with dollar-2: {reader.password[:2]}')
                print(f'Contains colon: {":" in reader.password}')
        else:
            print('Reader R001 not found')

asyncio.run(check())
