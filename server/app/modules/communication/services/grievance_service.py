from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.communication_models import GrievanceTicket, GrievanceComment
from app.modules.communication.schemas import GrievanceCreate, GrievanceCommentCreate
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import NotificationCreate

class GrievanceService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def create_ticket(self, data: GrievanceCreate, submitter_id: UUID, submitter_type: str) -> GrievanceTicket:
        ticket = GrievanceTicket(
            tenant_id=self.tenant_id,
            submitter_id=submitter_id,
            submitter_type=submitter_type,
            category=data.category,
            subject=data.subject,
            description=data.description,
            priority=data.priority,
            status='open'
        )
        self.db.add(ticket)
        await self.db.commit()
        # Notify admins – for simplicity, we'll post a notification to a default admin role.
        return ticket

    async def add_comment(self, ticket_id: UUID, comment: str, author_id: UUID, author_type: str) -> GrievanceComment:
        gc = GrievanceComment(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            author_id=author_id,
            author_type=author_type,
            comment=comment
        )
        self.db.add(gc)
        await self.db.commit()
        return gc

    async def get_ticket(self, ticket_id: UUID) -> Optional[GrievanceTicket]:
        ticket = await self.db.get(GrievanceTicket, ticket_id)
        if ticket and ticket.tenant_id == self.tenant_id:
            return ticket
        return None

    async def list_user_tickets(self, user_id: UUID) -> List[GrievanceTicket]:
        stmt = select(GrievanceTicket).where(
            GrievanceTicket.submitter_id == user_id,
            GrievanceTicket.tenant_id == self.tenant_id
        ).order_by(GrievanceTicket.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_comments(self, ticket_id: UUID) -> List[GrievanceComment]:
        stmt = select(GrievanceComment).where(GrievanceComment.ticket_id == ticket_id, GrievanceComment.tenant_id == self.tenant_id).order_by(GrievanceComment.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()