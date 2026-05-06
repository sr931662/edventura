from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text, update
from app.models.attendance_models import (
    AttendanceRecord, AttendancePolicy, TeacherClassAssignment,
    EmployeePunchLog, ShiftSchedule, AttendanceComputation,
    AttendanceRecoverySession, Device, BiometricTemplate,
    QRCheckinLog, BLENFCLog, TransportAttendance, HostelMovement,
    EmployeeLeave, AdvancedAttendanceAnalytics,
    ComplianceDocument, AttendanceAuditLog, TenantBranding,
    ConsolidatedAttendance
)
from typing import Optional, List
from uuid import UUID
from datetime import date, timedelta

class AttendanceRepository:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ---------- Core Marking ----------
    async def bulk_mark(self, data: dict) -> List[AttendanceRecord]:
        records = []
        for entry in data['entries']:
            rec = AttendanceRecord(
                tenant_id=self.tenant_id,
                student_id=entry.get('student_id'),
                employee_id=entry.get('employee_id'),
                attendance_type=data['attendance_type'],
                date=data['date'],
                in_time=entry.get('in_time'),
                out_time=entry.get('out_time'),
                status=entry['status'],
                period_number=data.get('period_number'),
                class_id=data.get('class_id'),
                marked_by=data['marked_by'],
                notes=entry.get('notes'),
                late_minutes=entry.get('late_minutes'),
                device_id=entry.get('device_id'),
                verification_method=entry.get('verification_method')
            )
            self.db.add(rec)
            records.append(rec)
        await self.db.commit()
        return records

    async def upsert_attendance_record(self, record: AttendanceRecord):
        stmt = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == self.tenant_id,
            AttendanceRecord.student_id == record.student_id,
            AttendanceRecord.date == record.date,
            AttendanceRecord.period_number == record.period_number
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            for key in ('status', 'in_time', 'late_minutes', 'notes', 'marked_by', 'marked_source'):
                setattr(existing, key, getattr(record, key))
            self.db.add(existing)
            await self.db.commit()
            return existing
        else:
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            return record

    # ---------- Policy ----------
    async def get_policy(self) -> Optional[AttendancePolicy]:
        stmt = select(AttendancePolicy).where(
            AttendancePolicy.tenant_id == self.tenant_id,
            AttendancePolicy.is_deleted == False
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_policy(self, config: dict) -> AttendancePolicy:
        policy = await self.get_policy()
        if policy:
            policy.config = config
        else:
            policy = AttendancePolicy(tenant_id=self.tenant_id, name="Default", config=config)
            self.db.add(policy)
        await self.db.commit()
        return policy

    # ---------- Teacher Assignments ----------
    async def get_teacher_assignments(self, teacher_id: UUID, marking_date: date) -> list:
        stmt = select(TeacherClassAssignment).where(
            TeacherClassAssignment.tenant_id == self.tenant_id,
            TeacherClassAssignment.teacher_id == teacher_id,
            TeacherClassAssignment.effective_from <= marking_date,
            (TeacherClassAssignment.effective_to == None) |
            (TeacherClassAssignment.effective_to >= marking_date),
            TeacherClassAssignment.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Recovery ----------
    async def get_students_below_attendance(self, min_percent: float, days=30) -> list:
        from_date = date.today() - timedelta(days=days)
        query = text("""
            SELECT s.id, s.first_name || ' ' || s.last_name as student_name,
                   COALESCE(COUNT(CASE WHEN ar.status = 'present' THEN 1 END) * 1.0 / NULLIF(COUNT(ar.id),0) * 100, 100) as att_percent
            FROM students s
            LEFT JOIN attendance_records ar ON s.id = ar.student_id
                AND ar.tenant_id = :tenant_id
                AND ar.date BETWEEN :from_date AND :to_date
                AND ar.attendance_type = 'student_class'
            WHERE s.tenant_id = :tenant_id AND s.is_active = true
            GROUP BY s.id
            HAVING COALESCE(COUNT(CASE WHEN ar.status = 'present' THEN 1 END) * 1.0 / NULLIF(COUNT(ar.id),0) * 100, 100) < :min_percent
        """)
        res = await self.db.execute(query, {
            "tenant_id": self.tenant_id,
            "from_date": from_date,
            "to_date": date.today(),
            "min_percent": min_percent
        })
        return [{"student_id": row.id, "student_name": row.student_name, "attendance_percent": round(row.att_percent,2)} for row in res]

    async def create_recovery_session(self, data: dict) -> AttendanceRecoverySession:
        session = AttendanceRecoverySession(tenant_id=self.tenant_id, **data)
        self.db.add(session)
        await self.db.commit()
        return session

    # ---------- Shifts ----------
    async def bulk_create_shifts(self, entries: list) -> list:
        schedules = [ShiftSchedule(tenant_id=self.tenant_id, **e) for e in entries]
        self.db.add_all(schedules)
        await self.db.commit()
        return schedules

    async def get_shifts_for_employee(self, employee_id: UUID, from_date: date, to_date: date) -> list:
        stmt = select(ShiftSchedule).where(
            ShiftSchedule.tenant_id == self.tenant_id,
            ShiftSchedule.employee_id == employee_id,
            ShiftSchedule.date >= from_date,
            ShiftSchedule.date <= to_date
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def detect_missed_punches(self, target_date: date) -> list:
        stmt = select(ShiftSchedule).where(
            ShiftSchedule.tenant_id == self.tenant_id,
            ShiftSchedule.date == target_date
        )
        shifts = (await self.db.execute(stmt)).scalars().all()
        missed = []
        for shift in shifts:
            rec = (await self.db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.tenant_id == self.tenant_id,
                    AttendanceRecord.employee_id == shift.employee_id,
                    AttendanceRecord.date == target_date,
                    AttendanceRecord.attendance_type == 'employee'
                )
            )).scalar_one_or_none()
            if not rec:
                missed.append(shift)
        return missed

    # ---------- Leaves ----------
    async def apply_leave(self, data: dict) -> EmployeeLeave:
        leave = EmployeeLeave(tenant_id=self.tenant_id, **data)
        self.db.add(leave)
        await self.db.commit()
        return leave

    async def approve_leave(self, leave_id: UUID, approved_by: UUID, status: str) -> Optional[EmployeeLeave]:
        leave = await self.db.get(EmployeeLeave, leave_id)
        if not leave or leave.tenant_id != self.tenant_id:
            return None
        leave.status = status
        leave.approved_by = approved_by
        await self.db.commit()
        return leave

    async def get_employee_leaves(self, employee_id: UUID) -> list:
        stmt = select(EmployeeLeave).where(
            EmployeeLeave.tenant_id == self.tenant_id,
            EmployeeLeave.employee_id == employee_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Hostel ----------
    async def record_hostel_movement(self, data: dict) -> HostelMovement:
        mv = HostelMovement(tenant_id=self.tenant_id, **data)
        self.db.add(mv)
        await self.db.commit()
        return mv

    async def get_student_movements(self, student_id: UUID) -> list:
        stmt = select(HostelMovement).where(
            HostelMovement.tenant_id == self.tenant_id,
            HostelMovement.student_id == student_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Transport ----------
    async def record_transport_scan(self, data: dict) -> TransportAttendance:
        ta = TransportAttendance(tenant_id=self.tenant_id, **data)
        self.db.add(ta)
        await self.db.commit()
        return ta

    # ---------- Analytics ----------
    async def aggregate_heatmap(self, class_id: UUID, week_start: date) -> List[AdvancedAttendanceAnalytics]:
        from datetime import timedelta
        stmt = select(AdvancedAttendanceAnalytics).where(
            AdvancedAttendanceAnalytics.tenant_id == self.tenant_id,
            AdvancedAttendanceAnalytics.class_id == class_id,
            AdvancedAttendanceAnalytics.date >= week_start,
            AdvancedAttendanceAnalytics.date < week_start + timedelta(days=7),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def compare_classes(self, class_ids: List[UUID], from_date: date, to_date: date) -> List[AdvancedAttendanceAnalytics]:
        stmt = select(AdvancedAttendanceAnalytics).where(
            AdvancedAttendanceAnalytics.tenant_id == self.tenant_id,
            AdvancedAttendanceAnalytics.class_id.in_(class_ids),
            AdvancedAttendanceAnalytics.date >= from_date,
            AdvancedAttendanceAnalytics.date <= to_date,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Devices ----------
    async def register_device(self, data: dict) -> Device:
        device = Device(tenant_id=self.tenant_id, **data)
        self.db.add(device)
        await self.db.commit()
        return device

    # ---------- Branding ----------
    async def get_branding(self) -> Optional[TenantBranding]:
        stmt = select(TenantBranding).where(TenantBranding.tenant_id == self.tenant_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def upsert_branding(self, data: dict) -> TenantBranding:
        branding = await self.get_branding()
        if branding:
            for k, v in data.items():
                setattr(branding, k, v)
        else:
            branding = TenantBranding(tenant_id=self.tenant_id, **data)
            self.db.add(branding)
        await self.db.commit()
        return branding