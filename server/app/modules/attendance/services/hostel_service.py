from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.attendance.repository import AttendanceRepository

class HostelService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = AttendanceRepository(db, tenant_id)

    async def record_movement(self, data: dict):
        return await self.repo.record_hostel_movement(data)

    async def get_student_movements(self, student_id: UUID):
        return await self.repo.get_student_movements(student_id)

    async def night_roll_call(self):
        from sqlalchemy import select
        from app.models.attendance_models import HostelMovement
        result = await self.repo.db.execute(
            select(HostelMovement).where(
                HostelMovement.tenant_id == self.repo.tenant_id,
                HostelMovement.type == 'out'
            )
        )
        return result.scalars().all()