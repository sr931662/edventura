import uuid
from sqlalchemy import Column, String, Date, Time, Boolean, Integer, Numeric, DateTime, Text, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import EdVenturaBase
from app.core.database import Base
import sqlalchemy as sa

# ------------------------------------------------------------
# Phase 1 core tables
# ------------------------------------------------------------
class AttendancePolicy(EdVenturaBase):
    __tablename__ = "attendance_policies"
    name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=False, default={})

class AttendanceRecord(EdVenturaBase):
    __tablename__ = "attendance_records"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    employee_id = Column(UUID(as_uuid=True), nullable=True)
    attendance_type = Column(String(30), nullable=False)               # student_class, employee, etc.
    date = Column(Date, nullable=False)
    in_time = Column(Time, nullable=True)
    out_time = Column(Time, nullable=True)
    status = Column(String(20), nullable=False, default="unmarked")    # present, absent, late, half_day, excused
    period_number = Column(Integer, nullable=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    section = Column(String(20), nullable=True)
    marked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    late_minutes = Column(Integer, nullable=True)
    device_id = Column(String(100), nullable=True)
    verification_method = Column(String(50), nullable=True)
    offline_marked_at = Column(DateTime(timezone=True), nullable=True)
    marked_source = Column(String(20), default="web")
    __table_args__ = (
        UniqueConstraint('student_id', 'date', 'period_number', 
                        name='uq_attendance_student_date_period'),
    )

class TeacherClassAssignment(EdVenturaBase):
    __tablename__ = "teacher_class_assignments"
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=True)
    period_number = Column(Integer, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

class EmployeePunchLog(Base):
    """doesn't need EdVenturaBase soft-delete"""
    __tablename__ = "employee_punch_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False)
    punch_time = Column(DateTime(timezone=True), nullable=False)
    type = Column(String(10), nullable=False)          # 'in' or 'out'
    location = Column(String(100), nullable=True)
    device_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ShiftSchedule(EdVenturaBase):
    __tablename__ = "shift_schedules"
    employee_id = Column(UUID(as_uuid=True), nullable=False)
    shift_id = Column(UUID(as_uuid=True), nullable=True)
    date = Column(Date, nullable=False)
    expected_in = Column(Time, nullable=False)
    expected_out = Column(Time, nullable=False)

class AttendanceComputation(EdVenturaBase):
    __tablename__ = "attendance_computations"
    student_id = Column(UUID(as_uuid=True), nullable=True)
    employee_id = Column(UUID(as_uuid=True), nullable=True)
    date = Column(Date, nullable=False)
    effective_present = Column(Boolean, default=False)
    computed_hours = Column(Numeric(5,2), nullable=True)
    attendance_percent = Column(Numeric(5,2), nullable=True)

class AttendanceRecoverySession(EdVenturaBase):
    __tablename__ = "attendance_recovery_sessions"
    subject_id = Column(UUID(as_uuid=True), nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    scheduled_date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    max_capacity = Column(Integer, default=30)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="proposed")

# ------------------------------------------------------------
# Phase 2+ tables (already present, kept for completeness)
# ------------------------------------------------------------
class Device(EdVenturaBase):
    __tablename__ = "devices"
    type = Column(String(30), nullable=False)
    location_desc = Column(Text)
    device_metadata = Column(JSON, nullable=False, default={})

class BiometricTemplate(EdVenturaBase):
    __tablename__ = "biometric_templates"
    user_id = Column(UUID, nullable=False)
    user_type = Column(String(20), nullable=False)
    template_data = Column(Text, nullable=False)
    device_type = Column(String(50))

class QRCheckinLog(Base):
    __tablename__ = "qr_checkin_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    student_id = Column(UUID, nullable=True)
    employee_id = Column(UUID, nullable=True)
    scan_time = Column(DateTime(timezone=True), nullable=False)
    device_id = Column(UUID, nullable=False)
    location = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BLENFCLog(Base):
    __tablename__ = "ble_nfc_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    student_id = Column(UUID, nullable=True)
    employee_id = Column(UUID, nullable=True)
    event_time = Column(DateTime(timezone=True), nullable=False)
    device_id = Column(UUID, nullable=False)
    signal_strength = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TransportAttendance(Base):
    __tablename__ = "transport_attendance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    student_id = Column(UUID, nullable=False)
    route_id = Column(UUID, nullable=False)
    vehicle_id = Column(UUID, nullable=False)
    boarding_time = Column(DateTime(timezone=True))
    alighting_time = Column(DateTime(timezone=True))
    boarding_stop = Column(String(100))
    alighting_stop = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class HostelMovement(Base):
    __tablename__ = "hostel_movement"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    student_id = Column(UUID, nullable=False)
    type = Column(String(10), nullable=False)
    time = Column(DateTime(timezone=True), nullable=False)
    gate_no = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EmployeeLeave(EdVenturaBase):
    __tablename__ = "employee_leave"
    employee_id = Column(UUID, nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    leave_type = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    approved_by = Column(UUID)

class AdvancedAttendanceAnalytics(Base):
    __tablename__ = "advanced_attendance_analytics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    class_id = Column(UUID, nullable=False)
    date = Column(Date, nullable=False)
    period_number = Column(Integer)
    present_count = Column(Integer, default=0)
    absent_count = Column(Integer, default=0)
    late_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    aggregated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Compliance, audit, branding (phase 4)
class ComplianceDocument(Base):
    __tablename__ = "compliance_documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), nullable=False)
    doc_type = Column(String(50), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    file_path = Column(String(500))
    status = Column(String(20), default='generated')
    created_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=sa.func.now())

class AttendanceAuditLog(Base):
    __tablename__ = "attendance_audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    action = Column(String(20), nullable=False)

class TenantBranding(Base):
    __tablename__ = "tenant_branding"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    logo_url = Column(String(500))
    primary_color = Column(String(7))
    secondary_color = Column(String(7))
    notification_templates = Column(JSON, default={})
    attendance_policy_override = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=sa.func.now())

class ConsolidatedAttendance(Base):
    __tablename__ = "consolidated_attendance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    child_tenant_id = Column(UUID(as_uuid=True), nullable=False)
    date = Column(Date, nullable=False)
    present_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    present_percent = Column(Numeric(5,2))
    updated_at = Column(DateTime(timezone=True), server_default=sa.func.now())