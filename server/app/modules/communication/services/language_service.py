from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import TemplateTranslation, CommunicationPreference
class LanguageService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_translation(self, template_id: UUID, lang_code: str) -> Optional[TemplateTranslation]:
        stmt = select(TemplateTranslation).where(
            TemplateTranslation.template_id == template_id,
            TemplateTranslation.language_code == lang_code,
            TemplateTranslation.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_translation(self, data: dict) -> TemplateTranslation:
        trans = TemplateTranslation(tenant_id=self.tenant_id, **data)
        self.db.add(trans)
        await self.db.commit()
        return trans

    async def get_user_language(self, user_id: UUID, user_type: str) -> str:
        pref = (await self.db.execute(
            select(CommunicationPreference).where(
                CommunicationPreference.user_id == user_id,
                CommunicationPreference.user_type == user_type,
                CommunicationPreference.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        return pref.language if pref and pref.language else 'en'