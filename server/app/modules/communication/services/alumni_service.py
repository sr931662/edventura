from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import AlumniRecord
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import NotificationCreate

class AlumniService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def add_alumnus(self, data: dict) -> AlumniRecord:
        record = AlumniRecord(tenant_id=self.tenant_id, **data)
        self.db.add(record)
        await self.db.commit()
        return record

    async def list_alumni(self, graduation_year: int = None) -> List[AlumniRecord]:
        stmt = select(AlumniRecord).where(AlumniRecord.tenant_id == self.tenant_id)
        if graduation_year:
            stmt = stmt.where(AlumniRecord.graduation_year == graduation_year)
        result = await self.db.execute(stmt.order_by(AlumniRecord.full_name))
        return result.scalars().all()

    async def broadcast_to_alumni(self, title: str, body: str):
        alumni = (await self.db.execute(
            select(AlumniRecord).where(AlumniRecord.tenant_id == self.tenant_id, AlumniRecord.opt_in_communication == True)
        )).scalars().all()
        count = 0
        for a in alumni:
            await self.notif_svc.send_notification(NotificationCreate(
                recipient_id=a.id, recipient_type="alumni",
                title=title, body=body, category="alumni", channel="in_app"
            ))
            count += 1
        return count