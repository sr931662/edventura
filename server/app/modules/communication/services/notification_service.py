import datetime
import logging
from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.communication_models import (
    Notification, CommunicationAuditLog, NotificationTemplate, CommunicationBranding,
)
from app.models.user import User
from app.modules.communication import schemas
from app.modules.communication.services.email_service import EmailService
import re

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def send_notification(self, data: schemas.NotificationCreate) -> Notification:
        notif = Notification(
            tenant_id=self.tenant_id,
            recipient_id=data.recipient_id,
            recipient_type=data.recipient_type,
            title=data.title,
            body=data.body,
            category=data.category,
            priority=data.priority,
            channel=data.channel,
            status='sent',
            meta_data=data.meta_data or {}
        )
        self.db.add(notif)
        await self.db.flush()
        self.db.add(CommunicationAuditLog(
            tenant_id=self.tenant_id,
            notification_id=notif.id,
            action='created',
            performed_by=data.recipient_id,
            details={'channel': data.channel, 'priority': data.priority}
        ))
        await self.db.commit()

        if data.channel == 'email':
            await self._dispatch_email(notif, data)

        return notif

    async def _dispatch_email(self, notif: Notification, data: schemas.NotificationCreate) -> None:
        """Resolve recipient email, build branded EmailService, attempt delivery."""
        to_email = data.recipient_email or await self._resolve_email(data.recipient_id, data.recipient_type)
        if not to_email:
            logger.warning(
                "No email address found for recipient %s (%s) — skipping email delivery",
                data.recipient_id, data.recipient_type,
            )
            return

        branding = await self._get_branding()
        email_svc = EmailService(
            sender_name=branding.sender_name if branding else None,
            sender_email=branding.sender_email if branding else None,
            primary_color=branding.primary_color if branding else "#4f46e5",
            logo_url=branding.logo_url if branding else None,
            footer_template=branding.footer_template if branding else None,
        )

        delivered = await email_svc.send(to_email, notif.title, notif.body)

        notif.status = 'delivered' if delivered else 'failed'
        if delivered:
            notif.delivered_at = datetime.datetime.utcnow()
        self.db.add(CommunicationAuditLog(
            tenant_id=self.tenant_id,
            notification_id=notif.id,
            action='email_delivered' if delivered else 'email_failed',
            performed_by=notif.recipient_id,
            details={'to': to_email},
        ))
        await self.db.commit()

    async def _resolve_email(self, recipient_id: UUID, recipient_type: str) -> Optional[str]:
        """Look up email from User table (covers student/parent/teacher/admin/staff)."""
        result = await self.db.execute(
            select(User.email).where(
                User.id == recipient_id,
                User.tenant_id == self.tenant_id,
                User.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _get_branding(self) -> Optional[CommunicationBranding]:
        result = await self.db.execute(
            select(CommunicationBranding).where(CommunicationBranding.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def send_from_template(self, template_name: str, recipient_id: UUID, recipient_type: str,
                                 variables: dict, priority: Optional[str] = None,
                                 channels: Optional[List[str]] = None, lang_code: str = 'en'):
        """Render a template and send notification."""
        template = (await self.db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.tenant_id == self.tenant_id,
                NotificationTemplate.name == template_name,
                NotificationTemplate.is_active == True
            )
        )).scalar_one_or_none()
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        trans = await self.language_svc.get_translation(template.id, lang_code) if hasattr(self, 'language_svc') else None
        title = trans.title_template if trans else template.title_template
        body = trans.body_template if trans else template.body_template

        title = self._render_template(title, variables)
        body = self._render_template(body, variables)

        notifications = []
        for channel in (channels or template.default_channels):
            notif = Notification(
                tenant_id=self.tenant_id,
                recipient_id=recipient_id,
                recipient_type=recipient_type,
                title=title,
                body=body,
                category=template.category,
                priority=priority or template.default_priority,
                channel=channel,
                status='sent',
                meta_data={'template': template_name, **variables}
            )
            self.db.add(notif)
            notifications.append(notif)
        await self.db.commit()

        for notif in notifications:
            if notif.channel == 'email':
                stub = schemas.NotificationCreate(
                    recipient_id=recipient_id,
                    recipient_type=recipient_type,
                    title=title, body=body,
                    category=template.category,
                    channel='email',
                )
                await self._dispatch_email(notif, stub)

        return {"sent": True}

    def _render_template(self, template_str: str, variables: dict) -> str:
        # Simple placeholder replacement: {{ key }}
        def replace(match):
            key = match.group(1).strip()
            return str(variables.get(key, match.group(0)))
        return re.sub(r"\{\{\s*(\w+)\s*\}\}", replace, template_str)

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        notif = await self.db.get(Notification, notification_id)
        if not notif or notif.tenant_id != self.tenant_id:
            return None
        notif.status = 'read'
        notif.read_at = datetime.datetime.utcnow()
        self.db.add(CommunicationAuditLog(
            tenant_id=self.tenant_id,
            notification_id=notif.id,
            action='read',
            performed_by=user_id
        ))
        await self.db.commit()
        return notif

    async def get_inbox(self, recipient_id: UUID, skip: int = 0, limit: int = 50) -> List[Notification]:
        stmt = select(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.recipient_id == recipient_id,
            Notification.is_deleted == False
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_unread_count(self, recipient_id: UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.tenant_id == self.tenant_id,
            Notification.recipient_id == recipient_id,
            Notification.status == 'sent',
            Notification.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0