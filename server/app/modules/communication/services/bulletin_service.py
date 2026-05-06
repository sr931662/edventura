from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import BulletinBoardPost
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import BulletinCreate, NotificationCreate
from datetime import datetime

class BulletinService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def publish(self, data: BulletinCreate, published_by: UUID) -> BulletinBoardPost:
        post = BulletinBoardPost(
            tenant_id=self.tenant_id,
            title=data.title,
            body=data.body,
            category=data.category,
            target_audience=data.target_audience or [],
            pinned=data.pinned,
            expires_at=data.expires_at,
            published_at=datetime.utcnow(),
            published_by=published_by
        )
        self.db.add(post)
        await self.db.commit()

        # Notify target audience
        audience = data.target_audience or []
        for entry in audience:
            user_id = entry.get('user_id')
            user_type = entry.get('user_type', 'student')
            if user_id:
                await self.notif_svc.send_notification(NotificationCreate(
                    recipient_id=user_id,
                    recipient_type=user_type,
                    title=f"New {data.category}: {data.title}",
                    body=data.body[:200],
                    category=data.category,
                    priority="medium",
                    channel="in_app"
                ))
        return post

    async def get_active_posts(self, category: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[BulletinBoardPost]:
        stmt = select(BulletinBoardPost).where(
            BulletinBoardPost.tenant_id == self.tenant_id,
            BulletinBoardPost.is_deleted == False,
            (BulletinBoardPost.expires_at == None) | (BulletinBoardPost.expires_at > datetime.utcnow())
        ).order_by(BulletinBoardPost.pinned.desc(), BulletinBoardPost.published_at.desc())
        if category:
            stmt = stmt.where(BulletinBoardPost.category == category)
        result = await self.db.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()