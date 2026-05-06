from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import Meeting
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import MeetingCreate, NotificationCreate
from datetime import datetime

class MeetingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def schedule_meeting(self, data: MeetingCreate, organizer_id: UUID) -> Meeting:
        participants = data.participants or []
        # Mark organizer as confirmed
        for p in participants:
            if p.get('user_id') == str(organizer_id):
                p['status'] = 'confirmed'
        meeting = Meeting(
            tenant_id=self.tenant_id,
            title=data.title,
            description=data.description,
            meeting_type=data.meeting_type,
            organizer_id=organizer_id,
            scheduled_at=data.scheduled_at,
            end_at=data.end_at,
            location=data.location,
            meeting_link=data.meeting_link,
            participants=participants
        )
        self.db.add(meeting)
        await self.db.commit()

        # Notify participants
        for p in participants:
            uid = p.get('user_id')
            if uid and uid != str(organizer_id):
                await self.notif_svc.send_notification(NotificationCreate(
                    recipient_id=UUID(uid),
                    recipient_type=p.get('user_type', 'staff'),
                    title=f"Meeting Invitation: {data.title}",
                    body=f"Scheduled for {data.scheduled_at}",
                    category="meeting",
                    priority="high",
                    channel="in_app",
                    meta_data={"meeting_id": str(meeting.id)}
                ))
        return meeting

    async def respond_to_invite(self, meeting_id: UUID, user_id: UUID, status: str) -> Optional[Meeting]:
        meeting = await self.db.get(Meeting, meeting_id)
        if not meeting or meeting.tenant_id != self.tenant_id:
            return None
        participants: list = list(meeting.participants or [])
        for p in participants:
            if p.get('user_id') == str(user_id):
                p['status'] = status
                break
        meeting.participants = participants
        await self.db.commit()
        return meeting

    async def get_upcoming_meetings(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Meeting]:
        now = datetime.utcnow()
        stmt = select(Meeting).where(
            Meeting.tenant_id == self.tenant_id,
            Meeting.is_deleted == False,
            Meeting.scheduled_at >= now
        ).order_by(Meeting.scheduled_at).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        # Filter those where user is participant
        meetings = []
        for m in result.scalars():
            if any(p.get('user_id') == str(user_id) for p in (m.participants or [])):
                meetings.append(m)
        return meetings