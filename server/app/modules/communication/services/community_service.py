from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.communication_models import CommunityGroup, CommunityGroupMember, CommunityEvent, EventRegistration
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import NotificationCreate
from datetime import datetime

class CommunityService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    # Groups
    async def create_group(self, data: dict, created_by: UUID) -> CommunityGroup:
        group = CommunityGroup(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(group)
        await self.db.commit()
        return group

    async def list_groups(self, group_type: Optional[str] = None) -> List[CommunityGroup]:
        stmt = select(CommunityGroup).where(CommunityGroup.tenant_id == self.tenant_id, CommunityGroup.is_deleted == False)
        if group_type:
            stmt = stmt.where(CommunityGroup.group_type == group_type)
        result = await self.db.execute(stmt)
        groups = result.scalars().all()
        return groups

    async def join_group(self, group_id: UUID, user_id: UUID, user_type: str):
        member = CommunityGroupMember(
            tenant_id=self.tenant_id,
            group_id=group_id,
            user_id=user_id,
            user_type=user_type,
            role='member'
        )
        self.db.add(member)
        await self.db.commit()

    # Events
    async def create_event(self, data: dict, created_by: UUID) -> CommunityEvent:
        event = CommunityEvent(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(event)
        await self.db.commit()
        # Notify group members
        if event.group_id:
            members = (await self.db.execute(
                select(CommunityGroupMember.user_id, CommunityGroupMember.user_type).where(
                    CommunityGroupMember.group_id == event.group_id
                )
            )).all()
            for uid, utype in members:
                await self.notif_svc.send_notification(NotificationCreate(
                    recipient_id=uid, recipient_type=utype,
                    title=f"New Event: {event.title}",
                    body=f"Scheduled for {event.start_time}",
                    category="community_event",
                    channel="in_app"
                ))
        return event

    async def register_for_event(self, event_id: UUID, user_id: UUID) -> EventRegistration:
        reg = EventRegistration(tenant_id=self.tenant_id, event_id=event_id, user_id=user_id)
        self.db.add(reg)
        await self.db.commit()
        return reg

    async def list_events(self, group_id: Optional[UUID] = None) -> List[CommunityEvent]:
        stmt = select(CommunityEvent).where(CommunityEvent.tenant_id == self.tenant_id)
        if group_id:
            stmt = stmt.where(CommunityEvent.group_id == group_id)
        result = await self.db.execute(stmt.order_by(CommunityEvent.start_time.desc()))
        return result.scalars().all()