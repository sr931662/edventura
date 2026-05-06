import secrets
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import ResultAccessCode, StudentPerformanceAnalytics

class ResultPublishingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def publish_result(self, student_id: UUID, exam_id: UUID) -> str:
        """Generate a unique access code and return it."""
        code = secrets.token_hex(6)[:12]
        access = ResultAccessCode(
            tenant_id=self.tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            access_code=code,
            is_used=False
        )
        self.db.add(access)
        await self.db.commit()
        return code

    async def get_result_by_code(self, access_code: str) -> Optional[dict]:
        access = (await self.db.execute(
            select(ResultAccessCode).where(
                ResultAccessCode.access_code == access_code,
                ResultAccessCode.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if not access:
            return None
        # Fetch performance
        perf = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == access.student_id,
                StudentPerformanceAnalytics.exam_id == access.exam_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if not perf:
            return None
        return {
            "student_id": str(access.student_id),
            "exam_id": str(access.exam_id),
            "marks": float(perf.marks_obtained),
            "total": float(perf.total_marks),
            "percentage": float(perf.percentage)
        }