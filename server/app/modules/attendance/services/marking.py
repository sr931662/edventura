from typing import List, Optional
from datetime import date, time, datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.attendance_models import AttendanceRecord, TeacherClassAssignment, ShiftSchedule, EmployeePunchLog
from app.models.student import Student
from app.models.class_ import Class
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.services.tenant_config import TenantConfigService
from app.modules.attendance.event_publisher import publish_event
from app.modules.attendance.services.audit_service import log_attendance_change

class AttendanceMarkingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.config = TenantConfigService(db, tenant_id)
        self.repo = AttendanceRepository(db, tenant_id)

    async def get_teacher_classes(self, teacher_id: UUID, marking_date: date) -> List[dict]:
        assignments = await self.repo.get_teacher_assignments(teacher_id, marking_date)
        classes = []
        for a in assignments:
            cls = await self.db.get(Class, a.class_id)
            if cls:
                classes.append({
                    "class_id": a.class_id,
                    "class_name": cls.name,
                    "section": cls.section,
                    "subject_id": a.subject_id,
                    "period_number": a.period_number
                })
        return classes

    async def get_students_for_marking(self, class_id: UUID, section: Optional[str] = None,
                                       marking_date: Optional[date] = None) -> List[dict]:
        stmt = select(Student).where(
            Student.tenant_id == self.tenant_id,
            Student.is_active == True,
            Student.class_id == class_id
        )
        if section:
            stmt = stmt.where(Student.section == section)
        result = await self.db.execute(stmt)
        students = result.scalars().all()

        prefill = {}
        if marking_date:
            existing = await self.db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.tenant_id == self.tenant_id,
                    AttendanceRecord.date == marking_date,
                    AttendanceRecord.class_id == class_id,
                    AttendanceRecord.student_id.in_([s.id for s in students])
                )
            )
            for r in existing.scalars():
                prefill[r.student_id] = r.status

        student_list = []
        for s in students:
            student_list.append({
                "student_id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "photo_url": None,
                "previous_status": prefill.get(s.id)
            })
        return student_list

    async def bulk_mark(self, payload: dict, marked_by: UUID) -> dict:
        marking_date = payload["date"]
        period_number = payload.get("period_number")
        offline_marked_at = payload.get("offline_marked_at")
        source = payload.get("source", "web")
        grace_minutes = (await self.config.get_config()).get("late_grace_minutes", 15)

        results = []
        conflicts = 0
        for entry in payload["entries"]:
            student_id = entry["student_id"]
            status = entry["status"]
            in_time = entry.get("in_time")
            notes = entry.get("notes")
            late_minutes = None

            # After event publish
            from app.modules.gamification.gamification_service import GamificationService
            gam = GamificationService(self.db, self.tenant_id)
            await gam.handle_attendance_event(student_id, status, marking_date)
            
            if status == "late" and in_time:
                # default start 08:00
                default_start = time(8, 0)
                actual_dt = datetime.combine(marking_date, in_time)
                expected_dt = datetime.combine(marking_date, default_start)
                diff = (actual_dt - expected_dt).seconds // 60
                if diff > 0:
                    late_minutes = diff
                    if diff <= grace_minutes:
                        status = "present"
                    else:
                        status = "late"

            rec = AttendanceRecord(
                tenant_id=self.tenant_id,
                student_id=student_id,
                attendance_type="student_class",
                date=marking_date,
                in_time=in_time,
                status=status,
                period_number=period_number,
                class_id=payload["class_id"],
                notes=notes,
                late_minutes=late_minutes,
                marked_by=marked_by,
                marked_source=source,
                offline_marked_at=offline_marked_at
            )

            # Check conflict
            existing_stmt = select(AttendanceRecord).where(
                AttendanceRecord.tenant_id == self.tenant_id,
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.date == marking_date,
                AttendanceRecord.period_number == period_number
            )
            existing = (await self.db.execute(existing_stmt)).scalar_one_or_none()
            if existing and offline_marked_at:
                if existing.updated_at and existing.updated_at > offline_marked_at:
                    results.append({"student_id": student_id, "status": status, "conflict": True, "message": "Server record newer"})
                    conflicts += 1
                    continue

            # Upsert through repo method that handles audit
            if existing:
                # audit old values
                old_status = existing.status
                existing.status = status
                existing.in_time = in_time if in_time else existing.in_time
                existing.late_minutes = late_minutes
                existing.notes = notes
                existing.marked_by = marked_by
                existing.marked_source = source
                existing.offline_marked_at = offline_marked_at
                await self.repo.upsert_attendance_record(existing)
                if old_status != status:
                    await log_attendance_change(self.db, self.tenant_id, existing.id, marked_by, 'status', old_status, status, 'UPDATE')
            else:
                new_rec = await self.repo.upsert_attendance_record(rec)
                await log_attendance_change(self.db, self.tenant_id, new_rec.id, marked_by, 'status', None, status, 'INSERT')

            results.append({"student_id": student_id, "status": status, "conflict": False})

            

            if status in ("absent", "late"):
                from app.modules.gamification.gamification_service import GamificationService
                gam = GamificationService(self.db, self.tenant_id)
                await gam.handle_attendance_event(student_id, status, marking_date)
                await publish_event("attendance_events", {
                    "type": "AttendanceMarkedEvent",
                    "tenant_id": str(self.tenant_id),
                    "student_id": str(student_id),
                    "date": marking_date.isoformat(),
                    "status": status,
                    "method": source
                })
            

        return {"processed": len(payload["entries"]), "conflicts": conflicts, "results": results}

    async def punch(self, employee_id: UUID, punch_type: str, timestamp: datetime, location: Optional[str] = None):
        # Simplified for Phase 1
        log = EmployeePunchLog(
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            punch_time=timestamp,
            type=punch_type,
            location=location
        )
        self.db.add(log)
        await self.db.commit()