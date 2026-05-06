import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import async_session_factory
from app.core.config import settings
from sqlalchemy import text

async def check():
    print(f"Connecting to: {settings.DATABASE_URL[:60]}...")
    async with async_session_factory() as s:
        result = await s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        ))
        tables = [r[0] for r in result.fetchall()]
        print(f"Total tables: {len(tables)}")
        for t in tables:
            print(f"  {t}")

        # Check for demo users
        try:
            result2 = await s.execute(text(
                "SELECT email FROM users WHERE email LIKE '%sunrise.demo%' LIMIT 3"
            ))
            rows = result2.fetchall()
            print(f"\nSunrise demo users found: {len(rows)}")
            for r in rows:
                print(f"  {r[0]}")
        except Exception as e:
            print(f"\nCould not query users: {e}")

asyncio.run(check())
