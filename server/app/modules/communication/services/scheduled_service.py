from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import NotificationTemplate, ScheduledMessage
from app.modules.communication.services.broadcast_service import BroadcastService
from app.modules.communication.schemas import BroadcastCreate
from datetime import datetime, timedelta

class ScheduledService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.broadcast = BroadcastService(db, tenant_id)

    async def schedule_message(self, data: dict, created_by: UUID) -> ScheduledMessage:
        sched = ScheduledMessage(
            tenant_id=self.tenant_id,
            name=data['name'],
            template_id=data.get('template_id'),
            recipient_query={
                "target_type": data['target_type'],
                "target_id": data.get('target_id'),
                "roles": data.get('roles', [])
            },
            scheduled_at=data['scheduled_at'],
            repeat_interval=data.get('repeat_interval'),
            created_by=created_by
        )
        self.db.add(sched)
        await self.db.commit()
        return sched

    async def process_due_schedules(self):
        """Called by Celery beat; sends all messages whose scheduled_at <= now."""
        now = datetime.utcnow()
        due = (await self.db.execute(
            select(ScheduledMessage).where(
                ScheduledMessage.status == 'pending',
                ScheduledMessage.scheduled_at <= now,
                ScheduledMessage.tenant_id == self.tenant_id
            )
        )).scalars().all()
        for sched in due:
            q = sched.recipient_query
            await self.broadcast.send_broadcast(
                BroadcastCreate(
                    name=f"Scheduled: {sched.name}",
                    target_type=q['target_type'],
                    target_id=q.get('target_id'),
                    roles=q.get('roles', []),
                    template_name=sched.template_id and (await self.db.execute(select(NotificationTemplate).where(NotificationTemplate.id == sched.template_id)).scalar_one_or_none()).name,
                    title=None,
                    body=None,
                    priority="medium",
                    channels=["in_app"]
                ),
                sched.created_by
            )
            sched.status = 'sent'
            # Handle repeat: create next instance
            if sched.repeat_interval:
                next_time = self._compute_next(sched.scheduled_at, sched.repeat_interval)
                if next_time:
                    new_sched = ScheduledMessage(
                        tenant_id=sched.tenant_id,
                        name=sched.name,
                        template_id=sched.template_id,
                        recipient_query=sched.recipient_query,
                        scheduled_at=next_time,
                        repeat_interval=sched.repeat_interval,
                        status='pending',
                        created_by=sched.created_by
                    )
                    self.db.add(new_sched)
        await self.db.commit()

    def _compute_next(self, from_time: datetime, interval: str) -> Optional[datetime]:
        if interval == 'daily':
            return from_time + timedelta(days=1)
        elif interval == 'weekly':
            return from_time + timedelta(weeks=1)
        elif interval == 'monthly':
            # Add ~30 days
            return from_time + timedelta(days=30)
        return None