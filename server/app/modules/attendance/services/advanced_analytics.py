from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.attendance.repository import AttendanceRepository
from datetime import date, timedelta
from typing import List
from sqlalchemy import select
from app.models.attendance_models import AdvancedAttendanceAnalytics

class AdvancedAnalyticsService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = AttendanceRepository(db, tenant_id)

    async def get_heatmap(self, class_id: UUID, week_start: date):
        return await self.aggregate_heatmap(class_id, week_start)

    async def aggregate_heatmap(self, class_id: UUID, week_start: date):
        stmt = select(AdvancedAttendanceAnalytics).where(
            AdvancedAttendanceAnalytics.tenant_id == self.repo.tenant_id,
            AdvancedAttendanceAnalytics.class_id == class_id,
            AdvancedAttendanceAnalytics.date >= week_start,
        )
        result = await self.repo.db.execute(stmt)
        return result.scalars().all()

    async def compare_classes(self, class_ids: List[UUID], from_date: date, to_date: date):
        return await self.repo.compare_classes(class_ids, from_date, to_date)