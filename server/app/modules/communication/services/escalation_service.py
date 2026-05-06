from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import EscalationRule, Notification
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import NotificationCreate
from datetime import datetime, timedelta

class EscalationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def check_escalations(self):
        """Check for unread critical notifications that have exceeded their timeout."""
        rules = (await self.db.execute(
            select(EscalationRule).where(EscalationRule.tenant_id == self.tenant_id, EscalationRule.is_active == True)
        )).scalars().all()
        for rule in rules:
            timeout = datetime.utcnow() - timedelta(minutes=rule.timeout_minutes)
            # Find unread notifications of this category older than timeout
            unread = (await self.db.execute(
                select(Notification).where(
                    Notification.tenant_id == self.tenant_id,
                    Notification.category == rule.category,
                    Notification.status == 'sent',  # not read
                    Notification.priority.in_(['high', 'urgent', 'emergency']),
                    Notification.created_at <= timeout
                )
            )).scalars().all()
            for notif in unread:
                # Escalate: send to escalate_to_role (e.g., principal) via specified channels
                await self.notif_svc.send_notification(NotificationCreate(
                    recipient_id=UUID("00000000-0000-0000-0000-000000000001"),  # placeholder; we'll need to find actual admin user
                    recipient_type=rule.escalate_to_role,
                    title=f"Escalated: {notif.title}",
                    body=f"Original recipient ({notif.recipient_id}) has not read notification sent {timeout.isoformat()}",
                    category=rule.category,
                    priority='urgent',
                    channel=rule.channels[0] if rule.channels else 'in_app'
                ))
                # Mark original as escalated? not needed but can update a meta field.