from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, time, datetime
from uuid import UUID

class AttendancePolicyOut(BaseModel):
    id: UUID
    name: str
    config: dict
    class Config:
        from_attributes = True

class AttendancePolicyUpdate(BaseModel):
    config: dict

class MarkEntry(BaseModel):
    student_id: UUID
    status: str = Field(..., pattern="^(present|absent|late|half_day|excused)$")
    in_time: Optional[time] = None
    notes: Optional[str] = None

class BulkMarkPayload(BaseModel):
    class_id: UUID
    date: date
    entries: List[MarkEntry]
    period_number: Optional[int] = None
    offline_marked_at: Optional[datetime] = None

class MarkResult(BaseModel):
    student_id: UUID
    status: str
    conflict: bool = False
    message: Optional[str] = None

class BulkMarkResponse(BaseModel):
    processed: int
    conflicts: int
    results: List[MarkResult]

class StudentMarkingInfo(BaseModel):
    student_id: UUID
    first_name: str
    last_name: str
    photo_url: Optional[str] = None
    previous_status: Optional[str] = None

class TeacherClassDTO(BaseModel):
    class_id: UUID
    class_name: str
    section: Optional[str] = None
    subject_id: Optional[UUID] = None
    period_number: Optional[int] = None

class PunchRequest(BaseModel):
    employee_id: UUID
    type: str = Field(..., pattern="^(in|out)$")
    timestamp: datetime
    location: Optional[str] = None  # "lat,lng"

class PunchResponse(BaseModel):
    id: UUID
    message: str

class DailyReport(BaseModel):
    total: int
    present: int
    absent: int
    late: int
    half_day: int
    excused: int

class StudentAttendanceHistory(BaseModel):
    date: date
    status: str
    attendance_type: str

class ShiftScheduleOut(BaseModel):
    id: UUID
    employee_id: UUID
    date: date
    expected_in: time
    expected_out: time

class RecoveryProposalGenerate(BaseModel):
    tenant_id: UUID  # will be auto from context, but for API clarity

class RecoverySessionOut(BaseModel):
    id: UUID
    subject_id: Optional[UUID]
    teacher_id: Optional[UUID]
    scheduled_date: date
    duration_minutes: int
    max_capacity: int
    reason: Optional[str]
    status: str
    
    


# ---- Device ----
class DeviceRegister(BaseModel):
    type: str = Field(..., pattern="^(biometric|qr|ble|nfc|gps|rfid)$")
    location_desc: Optional[str] = None
    device_metadata: Optional[dict] = None  # renamed from metadata

class DeviceOut(BaseModel):
    id: UUID
    tenant_id: UUID
    type: str
    location_desc: Optional[str]
    metadata: Optional[dict]
    class Config:
        from_attributes = True

# ---- Biometric ----
class BiometricTemplateUpload(BaseModel):
    user_id: UUID
    user_type: str = Field(..., pattern="^(student|employee)$")
    template_data: str   # encrypted
    device_type: Optional[str] = None

class BiometricTemplateOut(BaseModel):
    id: UUID
    user_id: UUID
    user_type: str
    class Config:
        from_attributes = True

# ---- QR / BLE NFC Scan ----
class QRScanRequest(BaseModel):
    code: str               # the decoded QR content (e.g., student UUID or unique ID)
    device_id: UUID
    scan_time: datetime
    location: Optional[str] = None   # "lat,lng"

class BLENFCEvent(BaseModel):
    device_id: UUID
    user_id: Optional[UUID] = None    # identified from beacon
    user_type: Optional[str] = None
    event_time: datetime
    signal_strength: Optional[int] = None

# ---- Transport ----
class TransportScan(BaseModel):
    student_id: UUID
    route_id: UUID
    vehicle_id: UUID
    type: str = Field(..., pattern="^(boarding|alighting)$")
    timestamp: datetime
    stop: Optional[str] = None

# ---- Hostel ----
class HostelMovementEntry(BaseModel):
    student_id: UUID
    type: str = Field(..., pattern="^(entry|exit)$")
    time: datetime
    gate_no: Optional[str] = None

# ---- Leave ----
class EmployeeLeaveApply(BaseModel):
    employee_id: UUID
    leave_type: str
    from_date: date
    to_date: date

class LeaveOut(BaseModel):
    id: UUID
    employee_id: UUID
    from_date: date
    to_date: date
    leave_type: str
    status: str
    class Config:
        from_attributes = True

class LeaveApproval(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")

# ---- Shifts ----
class ShiftCreate(BaseModel):
    employee_id: UUID
    date: date
    expected_in: time
    expected_out: time
    shift_id: Optional[UUID] = None

class ShiftOut(BaseModel):
    id: UUID
    employee_id: UUID
    date: date
    expected_in: time
    expected_out: time
    class Config:
        from_attributes = True

class BulkShiftCreate(BaseModel):
    entries: List[ShiftCreate]

class MissedPunchCorrection(BaseModel):
    employee_id: UUID
    date: date
    actual_in: Optional[datetime] = None
    actual_out: Optional[datetime] = None
    reason: Optional[str] = None

# ---- Analytics ----
class HeatmapData(BaseModel):
    period_number: int
    day_of_week: int   # 0=Monday
    present_percent: float

class ComparativeAnalyticsRequest(BaseModel):
    class_ids: List[UUID]
    from_date: date
    to_date: date

class ClassAttendanceComp(BaseModel):
    class_id: UUID
    class_name: str
    present_percent: float

    
class PayrollReport(BaseModel):
    employee_id: UUID
    from_date: date
    to_date: date
    days_present: int
    days_absent: int
    late_days: int
    overtime_hours: float
    approved_leave_days: int

class ExamEligibility(BaseModel):
    student_id: UUID
    eligible: bool
    attendance_percent: float
    min_required: float

class ExamMarkPayload(BaseModel):
    exam_id: UUID
    date: date
    student_ids: List[UUID]

class TransportReconciliationRequest(BaseModel):
    date: date
    route_id: UUID

class ParentDigestRecipient(BaseModel):
    student_id: UUID
    parent_email: Optional[str]
    parent_phone: Optional[str]

class BoardReportRequest(BaseModel):
    board_type: str
    academic_year: str
    output_format: str = "pdf"

class AuditLogEntry(BaseModel):
    id: UUID
    record_id: UUID
    changed_by: UUID
    changed_at: datetime
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    action: str

class BrandingOut(BaseModel):
    tenant_id: UUID
    logo_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    notification_templates: dict
    attendance_policy_override: dict

class ConsolidatedOut(BaseModel):
    date: date
    present_percent: float
    total_students: int