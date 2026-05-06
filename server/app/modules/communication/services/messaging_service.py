import datetime
from uuid import UUID
from typing import List, Optional
from celery import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import DirectMessage, MessageAttachment
from app.modules.communication import schemas
import os
from app.core.config import settings

class MessagingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def send_message(self, data: schemas.DirectMessageCreate, sender_id: UUID, sender_role: str) -> DirectMessage:
        msg = DirectMessage(
            tenant_id=self.tenant_id,
            sender_id=sender_id,
            sender_role=sender_role,
            receiver_id=data.receiver_id,
            receiver_role=data.receiver_role,
            subject=data.subject,
            body=data.body,
            priority=data.priority
        )
        self.db.add(msg)
        await self.db.flush()
        # If attachments provided, link them (we'll handle attachment upload separately)
        if data.attachments:
            for att_id in data.attachments:
                att = await self.db.get(MessageAttachment, att_id)
                if att:
                    att.message_type = 'direct_message'
                    att.message_id = msg.id
        await self.db.commit()
        return msg

    async def get_conversation(self, user1_id: UUID, user2_id: UUID, skip: int = 0, limit: int = 50) -> List[DirectMessage]:
        stmt = select(DirectMessage).where(
            DirectMessage.tenant_id == self.tenant_id,
            ((DirectMessage.sender_id == user1_id) & (DirectMessage.receiver_id == user2_id)) |
            ((DirectMessage.sender_id == user2_id) & (DirectMessage.receiver_id == user1_id))
        ).order_by(DirectMessage.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def mark_read(self, message_id: UUID, user_id: UUID) -> Optional[DirectMessage]:
        msg = await self.db.get(DirectMessage, message_id)
        if not msg or msg.tenant_id != self.tenant_id:
            return None
        if msg.receiver_id == user_id:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
            await self.db.commit()
        return msg

    async def upload_attachment(self, file_data: bytes, file_name: str, content_type: str) -> MessageAttachment:
        # Save file to media/attachments
        os.makedirs(os.path.join(settings.MEDIA_ROOT, "attachments"), exist_ok=True)
        file_path = os.path.join(settings.MEDIA_ROOT, "attachments", f"{uuid.uuid4()}_{file_name}")
        with open(file_path, "wb") as f:
            f.write(file_data)
        att = MessageAttachment(
            tenant_id=self.tenant_id,
            message_type='direct_message',
            message_id=None,  # will be set later
            file_name=file_name,
            file_path=file_path,
            content_type=content_type,
            file_size=len(file_data)
        )
        self.db.add(att)
        await self.db.commit()
        return att