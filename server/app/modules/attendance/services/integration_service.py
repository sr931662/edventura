from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.attendance_models import AttendanceRecord, AttendanceComputation, EmployeeLeave, ShiftSchedule, EmployeePunchLog
from app.models.student import Student
from app.modules.attendance.event_publisher import publish_event
from uuid import UUID
from datetime import date, datetime, timedelta
import httpx
from app.models.attendance_models import TransportAttendance

class IntegrationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ---- Payroll ----
    async def get_employee_payroll_report(self, employee_id: UUID, from_date: date, to_date: date):
        # Query attendance records for employee
        recs = await self.db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.tenant_id == self.tenant_id,
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date >= from_date,
                AttendanceRecord.date <= to_date,
                AttendanceRecord.attendance_type == 'employee'
            )
        )
        records = recs.scalars().all()
        present = sum(1 for r in records if r.status in ('present','late'))
        absent = sum(1 for r in records if r.status == 'absent')
        late = sum(1 for r in records if r.status == 'late')
        # Overtime from shift difference
        overtime_hours = 0.0
        # Compute overtime by comparing actual out-in with expected shift
        # For simplicity we'll sum extra hours from records where out_time > expected_out
        for r in records:
            if r.status in ('present','late') and r.in_time and r.out_time:
                shift = (await self.db.execute(
                    select(ShiftSchedule).where(
                        ShiftSchedule.employee_id == employee_id,
                        ShiftSchedule.date == r.date
                    )
                )).scalar_one_or_none()
                if shift:
                    expected_hours = (datetime.combine(r.date, shift.expected_out) - datetime.combine(r.date, shift.expected_in)).seconds / 3600
                    actual_hours = (datetime.combine(r.date, r.out_time) - datetime.combine(r.date, r.in_time)).seconds / 3600
                    if actual_hours > expected_hours:
                        overtime_hours += actual_hours - expected_hours
        leaves = await self.db.execute(
            select(EmployeeLeave).where(
                EmployeeLeave.employee_id == employee_id,
                EmployeeLeave.status == 'approved',
                EmployeeLeave.from_date <= to_date,
                EmployeeLeave.to_date >= from_date
            )
        )
        leave_days = 0
        for l in leaves.scalars():
            start = max(l.from_date, from_date)
            end = min(l.to_date, to_date)
            leave_days += (end - start).days + 1
        return {
            "employee_id": employee_id,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "days_present": present,
            "days_absent": absent,
            "late_days": late,
            "overtime_hours": round(overtime_hours, 2),
            "approved_leave_days": leave_days
        }

    # ---- Exam ----
    async def check_exam_eligibility(self, student_id: UUID):
        # get attendance percent from recent 30 days or as per policy
        comps = await self.db.execute(
            select(func.avg(AttendanceComputation.attendance_percent))
            .where(AttendanceComputation.student_id == student_id, AttendanceComputation.tenant_id == self.tenant_id)
        )
        avg = comps.scalar() or 100
        min_req = 75.0  # could be from policy
        eligible = avg >= min_req
        return {
            "student_id": student_id,
            "eligible": eligible,
            "attendance_percent": round(avg, 2),
            "min_required": min_req
        }

    async def mark_exam_attendance(self, exam_id: UUID, exam_date: date, student_ids: list[UUID], marked_by: UUID):
        records = []
        for sid in student_ids:
            record = AttendanceRecord(
                tenant_id=self.tenant_id,
                student_id=sid,
                attendance_type='exam',
                date=exam_date,
                status='present',  # default, can be overridden later
                marked_by=marked_by,
                marked_source='exam_module'
            )
            self.db.add(record)
            records.append(record)
        await self.db.commit()
        # Publish event
        await publish_event("attendance_events", {
            "type": "ExamAttendanceMarkedEvent",
            "tenant_id": str(self.tenant_id),
            "exam_id": str(exam_id),
            "date": exam_date.isoformat()
        })
        return len(records)

    # ---- Transport Reconciliation ----
    async def reconcile_transport(self, date: date, route_id: UUID):
        # Find students marked present in class but not boarded the bus for that route
        present_students = await self.db.execute(
            select(AttendanceRecord.student_id).where(
                AttendanceRecord.tenant_id == self.tenant_id,
                AttendanceRecord.date == date,
                AttendanceRecord.attendance_type == 'student_class',
                AttendanceRecord.status == 'present'
            )
        )
        present_ids = [r.student_id for r in present_students]
        # students who boarded on that route
        boarded = await self.db.execute(
            select(TransportAttendance.student_id).where(
                TransportAttendance.tenant_id == self.tenant_id,
                TransportAttendance.route_id == route_id,
                func.date(TransportAttendance.boarding_time) == date
            )
        )
        boarded_ids = [r.student_id for r in boarded]
        missing = [sid for sid in present_ids if sid not in boarded_ids]
        # Publish anomaly if any
        for sid in missing:
            await publish_event("attendance_events", {
                "type": "TransportReconciliationAnomaly",
                "student_id": str(sid),
                "date": date.isoformat()
            })
        return {"missing_boarders": len(missing)}

    # ---- Parent Digest ----
    async def send_parent_digest(self, target_date: date):
        # find all absent/late students today, group by class, send digest to parents
        # This would call notification service; here we just prepare payload
        absent_records = await self.db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.tenant_id == self.tenant_id,
                AttendanceRecord.date == target_date,
                AttendanceRecord.attendance_type == 'student_class',
                AttendanceRecord.status.in_(['absent','late'])
            )
        )
        records = absent_records.scalars().all()
        return {"queued": len(records)}

    # ---- Counselor Referral ----
    async def refer_to_counselor(self, student_id: UUID, reason: str):
        # In a real microservice environment, this would call the counselor module API.
        # For now, we publish an event.
        await publish_event("attendance_events", {
            "type": "CounselorReferralSuggested",
            "tenant_id": str(self.tenant_id),
            "student_id": str(student_id),
            "reason": reason
        })