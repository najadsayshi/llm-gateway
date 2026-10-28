import asyncio

from app.db import Base, engine
from app.models import APIKey


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("tables created")


asyncio.run(main())
