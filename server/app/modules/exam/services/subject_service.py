from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import Subject, Topic

class SubjectService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_subject(self, data: dict) -> Subject:
        subject = Subject(tenant_id=self.tenant_id, **data)
        self.db.add(subject)
        await self.db.commit()
        return subject

    async def list_subjects(self) -> list:
        stmt = select(Subject).where(Subject.tenant_id == self.tenant_id, Subject.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_topic(self, data: dict) -> Topic:
        topic = Topic(tenant_id=self.tenant_id, **data)
        self.db.add(topic)
        await self.db.commit()
        return topic

    async def list_topics(self, subject_id: UUID) -> list:
        stmt = select(Topic).where(Topic.tenant_id == self.tenant_id, Topic.subject_id == subject_id, Topic.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalars().all()