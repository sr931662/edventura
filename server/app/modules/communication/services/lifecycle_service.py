from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import CommunicationLifecycle

class LifecycleService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create(self, entity_type: str, entity_id: UUID, created_by: UUID) -> CommunicationLifecycle:
        lc = CommunicationLifecycle(
            tenant_id=self.tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            current_stage='draft',
            submitted_by=created_by
        )
        self.db.add(lc)
        await self.db.commit()
        return lc

    async def submit_for_approval(self, lifecycle_id: UUID, submitted_by: UUID) -> Optional[CommunicationLifecycle]:
        lc = await self.db.get(CommunicationLifecycle, lifecycle_id)
        if lc and lc.tenant_id == self.tenant_id:
            lc.current_stage = 'submitted'
            lc.submitted_by = submitted_by
            await self.db.commit()
        return lc

    async def approve(self, lifecycle_id: UUID, approved_by: UUID) -> Optional[CommunicationLifecycle]:
        lc = await self.db.get(CommunicationLifecycle, lifecycle_id)
        if lc and lc.tenant_id == self.tenant_id:
            lc.current_stage = 'approved'
            lc.approved_by = approved_by
            await self.db.commit()
        return lc

    async def publish(self, lifecycle_id: UUID) -> Optional[CommunicationLifecycle]:
        lc = await self.db.get(CommunicationLifecycle, lifecycle_id)
        if lc and lc.tenant_id == self.tenant_id and lc.current_stage == 'approved':
            lc.current_stage = 'published'
            await self.db.commit()
        return lc

    async def archive(self, lifecycle_id: UUID) -> Optional[CommunicationLifecycle]:
        lc = await self.db.get(CommunicationLifecycle, lifecycle_id)
        if lc and lc.tenant_id == self.tenant_id:
            lc.current_stage = 'archived'
            await self.db.commit()
        return lc

    async def reject(self, lifecycle_id: UUID, reason: str, rejected_by: UUID) -> Optional[CommunicationLifecycle]:
        lc = await self.db.get(CommunicationLifecycle, lifecycle_id)
        if lc and lc.tenant_id == self.tenant_id:
            lc.current_stage = 'rejected'
            lc.rejection_reason = reason
            lc.approved_by = rejected_by
            await self.db.commit()
        return lc

    async def get(self, entity_type: str, entity_id: UUID) -> Optional[CommunicationLifecycle]:
        stmt = select(CommunicationLifecycle).where(
            CommunicationLifecycle.tenant_id == self.tenant_id,
            CommunicationLifecycle.entity_type == entity_type,
            CommunicationLifecycle.entity_id == entity_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()