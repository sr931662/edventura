from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import CommunicationBranding

class CommunicationBrandingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_branding(self) -> Optional[CommunicationBranding]:
        stmt = select(CommunicationBranding).where(CommunicationBranding.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_branding(self, data: dict) -> CommunicationBranding:
        branding = await self.get_branding()
        if branding:
            for k, v in data.items():
                setattr(branding, k, v)
        else:
            branding = CommunicationBranding(tenant_id=self.tenant_id, **data)
            self.db.add(branding)
        await self.db.commit()
        return branding