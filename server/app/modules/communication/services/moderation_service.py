from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import Notification, DirectMessage

class ModerationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def moderate_message(self, message_type: str, message_id: UUID, action: str, moderator_id: UUID, reason: str = None) -> bool:
        if message_type == 'notification':
            msg = await self.db.get(Notification, message_id)
        elif message_type == 'direct_message':
            msg = await self.db.get(DirectMessage, message_id)
        else:
            return False
        if not msg or msg.tenant_id != self.tenant_id:
            return False
        if action == 'approve':
            msg.is_moderated = True
            msg.moderated_by = moderator_id
        elif action == 'flag':
            msg.is_moderated = False   # flagged, not approved
            msg.moderated_by = moderator_id
        await self.db.commit()
        return True