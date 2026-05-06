from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.event_publisher import publish_event
from datetime import date, datetime
from typing import List
from app.models.attendance_models import AttendanceRecord

class ShiftService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = AttendanceRepository(db, tenant_id)

    async def bulk_create_schedules(self, entries: List[dict]):
        return await self.repo.bulk_create_shifts(entries)

    async def get_employee_schedules(self, employee_id: UUID, from_date: date, to_date: date):
        return await self.repo.get_shifts_for_employee(employee_id, from_date, to_date)

    async def detect_missed_punches(self, target_date: date):
        missed = await self.repo.detect_missed_punches(target_date)
        for s in missed:
            await publish_event("attendance_events", {
                "type": "MissedPunchEvent",
                "tenant_id": str(self.repo.tenant_id),
                "employee_id": str(s.employee_id),
                "date": target_date.isoformat()
            })
        return missed

    async def correct_missed_punch(self, data: dict):
        # create a present record for that employee+date
        record = AttendanceRecord(
            tenant_id=self.repo.tenant_id,
            employee_id=data["employee_id"],
            attendance_type="employee",
            date=data["date"],
            in_time=data.get("actual_in"),
            out_time=data.get("actual_out"),
            status="present",
            marked_by=data.get("supervisor_id", data["employee_id"]),
            marked_source="manual_correction"
        )
        await self.repo.upsert_attendance_record(record)