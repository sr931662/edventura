from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import OfflineSyncQueue

class OfflineSyncService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def enqueue(self, user_id: UUID, message_type: str, payload: dict):
        item = OfflineSyncQueue(
            tenant_id=self.tenant_id,
            user_id=user_id,
            message_type=message_type,
            payload=payload,
            status='pending'
        )
        self.db.add(item)
        await self.db.commit()

    async def get_pending_for_user(self, user_id: UUID) -> list:
        stmt = select(OfflineSyncQueue).where(
            OfflineSyncQueue.tenant_id == self.tenant_id,
            OfflineSyncQueue.user_id == user_id,
            OfflineSyncQueue.status == 'pending'
        ).order_by(OfflineSyncQueue.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def mark_synced(self, queue_id: UUID):
        item = await self.db.get(OfflineSyncQueue, queue_id)
        if item and item.tenant_id == self.tenant_id:
            item.status = 'synced'
            await self.db.commit()