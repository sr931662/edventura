from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.attendance_models import AttendanceRecord
from uuid import UUID
from datetime import date

class ReportingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def daily_class_report(self, class_id: UUID, report_date: date) -> dict:
        base = and_(
            AttendanceRecord.tenant_id == self.tenant_id,
            AttendanceRecord.date == report_date,
            AttendanceRecord.class_id == class_id,
            AttendanceRecord.attendance_type == "student_class"
        )
        total = (await self.db.execute(select(func.count()).where(base))).scalar() or 0
        present = (await self.db.execute(select(func.count()).where(and_(base, AttendanceRecord.status == "present")))).scalar() or 0
        absent = (await self.db.execute(select(func.count()).where(and_(base, AttendanceRecord.status == "absent")))).scalar() or 0
        late = (await self.db.execute(select(func.count()).where(and_(base, AttendanceRecord.status == "late")))).scalar() or 0
        half_day = (await self.db.execute(select(func.count()).where(and_(base, AttendanceRecord.status == "half_day")))).scalar() or 0
        excused = (await self.db.execute(select(func.count()).where(and_(base, AttendanceRecord.status == "excused")))).scalar() or 0
        return {"total": total, "present": present, "absent": absent, "late": late, "half_day": half_day, "excused": excused}

    async def student_history(self, student_id: UUID, from_date: date, to_date: date) -> list:
        stmt = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == self.tenant_id,
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.date >= from_date,
            AttendanceRecord.date <= to_date
        ).order_by(AttendanceRecord.date)
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [{"date": r.date, "status": r.status, "attendance_type": r.attendance_type} for r in records]