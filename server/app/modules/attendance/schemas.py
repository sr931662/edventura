from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime
from uuid import UUID

# Base
class AttendanceMarkEntry(BaseModel):
    student_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    status: str = Field(..., pattern="^(present|absent|late|half_day|excused)$")
    in_time: Optional[time] = None
    out_time: Optional[time] = None
    period_number: Optional[int] = None
    notes: Optional[str] = None

class BulkAttendanceCreate(BaseModel):
    attendance_type: str = "student_class"  # from AttendanceType enum
    date: date
    class_id: Optional[UUID] = None
    hostel_id: Optional[UUID] = None
    transport_route_id: Optional[UUID] = None
    entries: List[AttendanceMarkEntry]
    period_number: Optional[int] = None

class AttendanceOut(BaseModel):
    id: UUID
    student_id: Optional[UUID]
    employee_id: Optional[UUID]
    attendance_type: str
    date: date
    in_time: Optional[time]
    out_time: Optional[time]
    status: str
    period_number: Optional[int]
    subject_id: Optional[UUID]
    class_id: Optional[UUID]
    section: Optional[str]
    hostel_id: Optional[UUID]
    transport_route_id: Optional[UUID]
    marked_by: UUID
    device_id: Optional[str]
    verification_method: Optional[str]
    notes: Optional[str]
    late_minutes: Optional[int]

    class Config:
        from_attributes = True

class AttendanceStats(BaseModel):
    total: int
    present: int
    absent: int
    late: int
    excused: int
    present_percent: float

class TrendPoint(BaseModel):
    date: date
    present_percent: float

class RiskStudent(BaseModel):
    student_id: UUID
    student_name: str
    attendance_percent: float
    risk_level: str  # 'low', 'medium', 'high'

# Employee
class EmployeeAttendanceMark(BaseModel):
    employee_id: UUID
    in_time: Optional[time] = None
    out_time: Optional[time] = None
    status: str
    shift_id: Optional[UUID] = None
    notes: Optional[str] = None

class BulkEmployeeMarkCreate(BaseModel):
    date: date
    entries: List[EmployeeAttendanceMark]

# Shift
class ShiftCreate(BaseModel):
    name: str
    start_time: time
    end_time: time
    applicable_to: str

class ShiftOut(BaseModel):
    id: UUID
    name: str
    start_time: time
    end_time: time
    applicable_to: str

    class Config:
        from_attributes = True

# Leave
class LeaveApply(BaseModel):
    user_id: UUID
    user_type: str
    from_date: date
    to_date: date
    leave_type: str

class LeaveOut(BaseModel):
    id: UUID
    user_id: UUID
    user_type: str
    from_date: date
    to_date: date
    leave_type: str
    status: str

    class Config:
        from_attributes = True

# Gamification
class AttendanceStreak(BaseModel):
    student_id: UUID
    current_streak: int
    longest_streak: int
    badge: Optional[str]

class LeaderboardEntry(BaseModel):
    class_id: UUID
    class_name: str
    present_percent: float

# Notification triggers
class NotificationTrigger(BaseModel):
    event: str  # "absent", "late", "low_attendance"
    user_type: str  # "parent", "teacher", "admin"
    template: str