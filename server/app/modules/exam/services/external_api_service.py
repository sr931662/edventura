from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import ExternalAPIKey
import hashlib

class ExternalAPIService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def register_api_key(self, provider: str, api_key: str) -> ExternalAPIKey:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        ext = ExternalAPIKey(
            tenant_id=self.tenant_id,
            provider=provider,
            api_key=key_hash
        )
        self.db.add(ext)
        await self.db.commit()
        return ext

    async def validate_api_key(self, provider: str, api_key: str) -> bool:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        stmt = select(ExternalAPIKey).where(
            ExternalAPIKey.tenant_id == self.tenant_id,
            ExternalAPIKey.provider == provider,
            ExternalAPIKey.api_key == key_hash,
            ExternalAPIKey.is_active == True
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def list_api_keys(self) -> list:
        stmt = select(ExternalAPIKey).where(ExternalAPIKey.tenant_id == self.tenant_id)
        res = await self.db.execute(stmt)
        return res.scalars().all()