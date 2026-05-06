from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.communication_models import AIOptimizationData, Notification
from datetime import datetime, timedelta

class AIOptimizationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def compute_optimal_send_time(self, user_id: UUID) -> dict:
        """Analyze past read times to find best hour for sending."""
        # Get read_at timestamps for this user
        notifications = (await self.db.execute(
            select(Notification.read_at).where(
                Notification.recipient_id == user_id,
                Notification.tenant_id == self.tenant_id,
                Notification.read_at != None
            )
        )).scalars().all()
        if not notifications:
            return {"best_send_hour": 9, "best_channel": "in_app", "confidence": "low"}

        # Most common hour of read
        hours = [n.hour for n in notifications if n]
        best_hour = max(set(hours), key=hours.count) if hours else 9

        # Best channel: count by channel
        channel_counts = {}
        channels_res = await self.db.execute(
            select(Notification.channel, func.count(Notification.id)).where(
                Notification.recipient_id == user_id,
                Notification.tenant_id == self.tenant_id,
                Notification.read_at != None
            ).group_by(Notification.channel)
        )
        for channel, count in channels_res:
            channel_counts[channel] = count
        best_channel = max(channel_counts, key=channel_counts.get) if channel_counts else "in_app"

        # Save to optimization data
        opt = (await self.db.execute(
            select(AIOptimizationData).where(AIOptimizationData.user_id == user_id, AIOptimizationData.tenant_id == self.tenant_id)
        )).scalar_one_or_none()
        if not opt:
            opt = AIOptimizationData(tenant_id=self.tenant_id, user_id=user_id)
            self.db.add(opt)
        opt.best_send_hour = best_hour
        opt.best_channel = best_channel
        opt.avg_open_time_minutes = 0  # simplify
        await self.db.commit()

        return {"best_send_hour": best_hour, "best_channel": best_channel, "confidence": "medium"}