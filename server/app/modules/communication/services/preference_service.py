from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import CommunicationPreference


class PreferenceService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_preferences(self, user_id: UUID, user_type: str) -> CommunicationPreference:
        stmt = select(CommunicationPreference).where(
            CommunicationPreference.tenant_id == self.tenant_id,
            CommunicationPreference.user_id == user_id,
            CommunicationPreference.user_type == user_type,
        )
        result = await self.db.execute(stmt)
        pref = result.scalar_one_or_none()
        if not pref:
            pref = CommunicationPreference(
                tenant_id=self.tenant_id,
                user_id=user_id,
                user_type=user_type,
            )
            self.db.add(pref)
            await self.db.commit()
            await self.db.refresh(pref)
        return pref

    async def update_preferences(self, user_id: UUID, user_type: str, data: dict) -> CommunicationPreference:
        pref = await self.get_preferences(user_id, user_type)
        for key, value in data.items():
            setattr(pref, key, value)
        await self.db.commit()
        await self.db.refresh(pref)
        return pref
