from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import BroadcastList, Notification
from app.models.student import Student
from app.models.user import User
from app.models.class_ import Class
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication import schemas

class BroadcastService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def send_broadcast(self, data: schemas.BroadcastCreate, created_by: UUID) -> dict:
        # Determine recipients
        recipients = await self._resolve_recipients(data.target_type, data.target_id, data.roles)
        # Send notifications to each recipient
        sent_count = 0
        for recipient in recipients:
            await self.notif_svc.send_notification(schemas.NotificationCreate(
                recipient_id=recipient['id'],
                recipient_type=recipient['type'],
                title=data.title or "Institution Announcement",
                body=data.body or "",
                category="broadcast",
                priority=data.priority,
                channel=data.channels[0]  # primary channel; others will be handled later
            ))
            sent_count += 1
        # Log broadcast
        broadcast = BroadcastList(
            tenant_id=self.tenant_id,
            name=data.name,
            target_type=data.target_type,
            target_id=data.target_id,
            roles=data.roles,
            created_by=created_by
        )
        self.db.add(broadcast)
        await self.db.commit()
        return {"recipient_count": sent_count, "broadcast_id": str(broadcast.id)}

    async def _resolve_recipients(self, target_type: str, target_id: UUID | None, roles: List[str]) -> List[dict]:
        recipients = []
        if target_type == "all":
            # Fetch all active users? For now, fetch all students and their parents
            students = (await self.db.execute(select(Student).where(Student.tenant_id == self.tenant_id, Student.is_active == True))).scalars().all()
            for s in students:
                recipients.append({"id": s.id, "type": "student"})
                # Also parents? For Phase2 we'll just target students.
        elif target_type == "class":
            students = (await self.db.execute(select(Student).where(Student.class_id == target_id, Student.tenant_id == self.tenant_id))).scalars().all()
            for s in students:
                recipients.append({"id": s.id, "type": "student"})
        elif target_type == "section":
            # target_id might be section id or we need to filter by section string; for now, assume class_id and section string
            # We'll skip for brevity but can be added.
            pass
        elif target_type == "role":
            # Fetch users with specific roles from user_roles table
            from app.models.user import User
            from app.models.user_role import user_roles
            if roles:
                stmt = select(User.id, User.full_name).select_from(user_roles).join(User, user_roles.c.user_id == User.id).where(user_roles.c.role_id.in_(roles), user_roles.c.tenant_id == self.tenant_id)
                users = (await self.db.execute(stmt)).all()
                for u in users:
                    recipients.append({"id": u.id, "type": "staff"})
        return recipients