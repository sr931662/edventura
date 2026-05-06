from uuid import UUID
from datetime import date
from typing import Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance import schemas


# ---------------------------------------------------------------------------
# Stubs for sub-services that are not yet built.
# Replace each class with a real implementation when the module is ready.
# ---------------------------------------------------------------------------

class _GamificationStub:
    def __init__(self, *_: Any) -> None: ...

    async def update_streak(self, *_: Any) -> None: ...

    async def get_streak(self, student_id: UUID) -> dict:
        return {
            "student_id": student_id,
            "current_streak": 0,
            "longest_streak": 0,
            "badge": None,
        }

    async def class_leaderboard(self, *_: Any) -> List[schemas.LeaderboardEntry]:
        return []


class _NotificationStub:
    async def send_parent_alert(self, *_: Any) -> None: ...


# ---------------------------------------------------------------------------

class AttendanceService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = AttendanceRepository(db, tenant_id)
        self.gam = _GamificationStub(db, tenant_id)
        self.notif = _NotificationStub()

    async def mark_bulk(
        self, data: schemas.BulkAttendanceCreate, marked_by: UUID
    ) -> List[schemas.AttendanceOut]:
        entries = [e.model_dump() for e in data.entries]
        records = await self.repo.bulk_mark({
            "class_id": data.class_id,
            "hostel_id": data.hostel_id,
            "transport_route_id": data.transport_route_id,
            "date": data.date,
            "entries": entries,
            "period_number": data.period_number,
            "attendance_type": data.attendance_type,
            "marked_by": marked_by,
        })
        for rec in records:
            sid: Any = rec.student_id
            status = str(rec.status)
            if sid is not None and status in ("absent", "late"):
                await self.notif.send_parent_alert(UUID(str(sid)), status)
        if data.attendance_type == "student_class":
            for rec in records:
                sid = rec.student_id
                await self.gam.update_streak(
                    UUID(str(sid)) if sid is not None else None,
                    str(rec.status),
                )
        return [schemas.AttendanceOut.model_validate(r) for r in records]

    async def get_class_attendance(
        self, class_id: UUID, on_date: date
    ) -> List[schemas.AttendanceOut]:
        records = await self.repo.get_class_attendance(class_id, on_date)
        return [schemas.AttendanceOut.model_validate(r) for r in records]

    async def get_student_attendance(
        self, student_id: UUID, from_date: date, to_date: date
    ) -> List[schemas.AttendanceOut]:
        records = await self.repo.get_student_attendance_range(student_id, from_date, to_date)
        return [schemas.AttendanceOut.model_validate(r) for r in records]

    async def get_employee_attendance(
        self, employee_id: UUID, from_date: date, to_date: date
    ) -> List[schemas.AttendanceOut]:
        records = await self.repo.get_employee_attendance(employee_id, from_date, to_date)
        return [schemas.AttendanceOut.model_validate(r) for r in records]

    async def get_daily_stats(
        self, on_date: date, attendance_type: str, class_id: Optional[UUID] = None
    ) -> schemas.AttendanceStats:
        stats = await self.repo.get_daily_stats(on_date, attendance_type, class_id)
        return schemas.AttendanceStats(**stats)

    async def get_trend(
        self, from_date: date, to_date: date, attendance_type: str, class_id: Optional[UUID] = None
    ) -> List[schemas.TrendPoint]:
        data = await self.repo.get_trend(from_date, to_date, attendance_type, class_id)
        return [schemas.TrendPoint(**d) for d in data]

    async def get_risk_students(
        self, threshold: float = 75.0, days: int = 30
    ) -> List[schemas.RiskStudent]:
        raw = await self.repo.get_risk_students(threshold, days)
        for r in raw:
            p = r["attendance_percent"]
            r["risk_level"] = "low" if p >= 60 else ("medium" if p >= 45 else "high")
        return [schemas.RiskStudent(**r) for r in raw]

    # Shift / Leave

    async def create_shift(self, shift: schemas.ShiftCreate) -> schemas.ShiftOut:
        s = await self.repo.create_shift(shift.model_dump())
        return schemas.ShiftOut.model_validate(s)

    async def get_shifts(self) -> List[schemas.ShiftOut]:
        shifts = await self.repo.get_shifts()
        return [schemas.ShiftOut.model_validate(s) for s in shifts]

    async def apply_leave(self, leave: schemas.LeaveApply) -> schemas.LeaveOut:
        l = await self.repo.apply_leave(leave.model_dump())
        return schemas.LeaveOut.model_validate(l)

    async def approve_leave(self, leave_id: UUID, approved_by: UUID) -> schemas.LeaveOut:
        l = await self.repo.approve_leave(leave_id, approved_by)
        if not l:
            raise ValueError("Leave not found")
        return schemas.LeaveOut.model_validate(l)

    # Gamification

    async def get_student_streak(self, student_id: UUID) -> schemas.AttendanceStreak:
        streak = await self.gam.get_streak(student_id)
        return schemas.AttendanceStreak(**streak)

    async def get_class_leaderboard(
        self, from_date: date, to_date: date
    ) -> List[schemas.LeaderboardEntry]:
        return await self.gam.class_leaderboard(from_date, to_date)

    # Policy

    async def get_policy(self) -> dict:
        policy = await self.repo.get_policy()
        return dict(policy.config) if policy else {}

    async def update_policy(self, config: dict) -> dict:
        policy = await self.repo.upsert_policy(config)
        return dict(policy.config) if policy else {}
