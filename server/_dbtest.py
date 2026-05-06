import asyncio, asyncpg, ssl
from app.core.config import settings

async def main():
    url = settings.DATABASE_URL.replace('postgresql+asyncpg', 'postgresql')
    ssl_ctx = ssl.create_default_context()
    conn = await asyncpg.connect(url, ssl=ssl_ctx)
    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_pending_secret VARCHAR(32)")
    print("Done. Columns now:")
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY column_name")
    print([r['column_name'] for r in cols])
    await conn.close()

asyncio.run(main())
