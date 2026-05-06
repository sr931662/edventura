from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.communication_models import CommunicationAnalytics, Notification

class CommunicationAnalyticsService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def update_analytics(self, user_id: UUID, user_type: str):
        # Aggregate from notifications
        total_sent = (await self.db.execute(
            select(func.count(Notification.id)).where(Notification.recipient_id == user_id, Notification.tenant_id == self.tenant_id)
        )).scalar() or 0
        total_read = (await self.db.execute(
            select(func.count(Notification.id)).where(Notification.recipient_id == user_id, Notification.status == 'read', Notification.tenant_id == self.tenant_id)
        )).scalar() or 0
        # Reputation: simple read rate
        read_rate = (total_read / total_sent * 100) if total_sent > 0 else 100
        rec = (await self.db.execute(
            select(CommunicationAnalytics).where(CommunicationAnalytics.user_id == user_id, CommunicationAnalytics.tenant_id == self.tenant_id)
        )).scalar_one_or_none()
        if not rec:
            rec = CommunicationAnalytics(tenant_id=self.tenant_id, user_id=user_id, user_type=user_type)
            self.db.add(rec)
        rec.total_sent = total_sent
        rec.total_read = total_read
        rec.reputation_score = read_rate
        await self.db.commit()
        return rec

    async def get_analytics(self, user_id: UUID) -> Optional[CommunicationAnalytics]:
        return (await self.db.execute(
            select(CommunicationAnalytics).where(CommunicationAnalytics.user_id == user_id, CommunicationAnalytics.tenant_id == self.tenant_id)
        )).scalar_one_or_none()