from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import NotificationTemplate

class TemplateService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_template(self, data: dict) -> NotificationTemplate:
        template = NotificationTemplate(tenant_id=self.tenant_id, **data)
        self.db.add(template)
        await self.db.commit()
        return template

    async def update_template(self, template_id: UUID, data: dict) -> Optional[NotificationTemplate]:
        tpl = await self.db.get(NotificationTemplate, template_id)
        if not tpl or tpl.tenant_id != self.tenant_id:
            return None
        for key, value in data.items():
            setattr(tpl, key, value)
        await self.db.commit()
        return tpl

    async def get_template(self, template_id: UUID) -> Optional[NotificationTemplate]:
        tpl = await self.db.get(NotificationTemplate, template_id)
        if tpl and tpl.tenant_id == self.tenant_id:
            return tpl
        return None

    async def list_templates(self, category: Optional[str] = None) -> List[NotificationTemplate]:
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.tenant_id == self.tenant_id,
            NotificationTemplate.is_deleted == False
        )
        if category:
            stmt = stmt.where(NotificationTemplate.category == category)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_template(self, template_id: UUID) -> bool:
        tpl = await self.db.get(NotificationTemplate, template_id)
        if not tpl or tpl.tenant_id != self.tenant_id:
            return False
        tpl.is_deleted = True
        await self.db.commit()
        return True