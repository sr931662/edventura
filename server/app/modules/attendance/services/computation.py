from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text, cast, Date
from app.models.attendance_models import AttendanceRecord, AttendanceComputation
from app.models.student import Student
from datetime import date, timedelta, datetime
from uuid import UUID
from typing import Optional
import numpy as np

class AttendanceComputationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def compute_daily(self, target_date: date):
        # For each student/employee with records on target_date, compute effective_present and computed_hours.
        # Then update rolling attendance percent.

        # 1. Get all active students
        students = (await self.db.execute(select(Student).where(Student.tenant_id == self.tenant_id, Student.is_active == True))).scalars().all()

        for student in students:
            # Fetch records for that student on target_date
            records = (await self.db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.tenant_id == self.tenant_id,
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.attendance_type == "student_class",
                    AttendanceRecord.date == target_date
                )
            )).scalars().all()

            effective_present = False
            computed_hours = None
            # Simplistic: If any record present, effective_present = True. real logic would use policy.
            if any(r.status in ("present", "late") for r in records):
                effective_present = True

            # Compute rolling 30-day attendance percent
            start_date = target_date - timedelta(days=30)
            count_stmt = select(func.count()).select_from(AttendanceRecord).where(
                AttendanceRecord.tenant_id == self.tenant_id,
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.attendance_type == "student_class",
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= target_date
            )
            total_days = (await self.db.execute(count_stmt.where())).scalar() or 1
            present_days = (await self.db.execute(
                count_stmt.where(AttendanceRecord.status.in_(["present", "late"]))
            )).scalar() or 0
            attendance_percent = (present_days / total_days * 100) if total_days > 0 else 100.0

            # Upsert into attendance_computations
            existing = (await self.db.execute(
                select(AttendanceComputation).where(
                    AttendanceComputation.tenant_id == self.tenant_id,
                    AttendanceComputation.student_id == student.id,
                    AttendanceComputation.date == target_date
                )
            )).scalar_one_or_none()

            if existing:
                existing.effective_present = effective_present
                existing.computed_hours = computed_hours
                existing.attendance_percent = attendance_percent
            else:
                self.db.add(AttendanceComputation(
                    tenant_id=self.tenant_id,
                    student_id=student.id,
                    date=target_date,
                    effective_present=effective_present,
                    computed_hours=computed_hours,
                    attendance_percent=attendance_percent
                ))

        # Similarly for employees – skipped for brevity, same pattern.
        await self.db.commit()

        # Publish event
        from app.modules.attendance.event_publisher import publish_event
        await publish_event("attendance_events", {
            "type": "DailyAttendanceComputedEvent",
            "tenant_id": str(self.tenant_id),
            "date": target_date.isoformat()
        })