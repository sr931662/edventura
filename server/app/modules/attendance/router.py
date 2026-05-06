from sqlalchemy import select

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_tenant
from app.core.permissions import PermissionChecker
from app.models.attendance_models import ConsolidatedAttendance
from app.models.user import User
from app.modules.attendance.services.tenant_config import TenantConfigService
from app.modules.attendance.services.marking import AttendanceMarkingService
from app.modules.attendance.services.reporting import ReportingService
from app.modules.attendance.services.recovery import RecoveryService
from app.modules.attendance.services.device_hub import DeviceHubService
from app.modules.attendance.services.shift_service import ShiftService
from app.modules.attendance.services.leave_service import LeaveService
from app.modules.attendance.services.hostel_service import HostelService
from app.modules.attendance.services.transport_service import TransportService
from app.modules.attendance.services.advanced_analytics import AdvancedAnalyticsService
from app.modules.attendance.services.integration_service import IntegrationService
from app.modules.attendance.services.compliance_service import ComplianceService
from app.modules.attendance.services.branding_service import BrandingService
from app.modules.attendance.attendance_schemas import (
    BulkMarkPayload, BulkMarkResponse, PunchRequest,
    DailyReport, StudentAttendanceHistory,
    AttendancePolicyOut, AttendancePolicyUpdate,
    TeacherClassDTO, StudentMarkingInfo,
    DeviceRegister, DeviceOut, BiometricTemplateUpload, BiometricTemplateOut,
    QRScanRequest, BLENFCEvent, TransportScan, TransportReconciliationRequest,
    HostelMovementEntry, EmployeeLeaveApply, LeaveOut, LeaveApproval,
    ShiftCreate, ShiftOut, BulkShiftCreate, MissedPunchCorrection,
    PayrollReport, ExamEligibility, ExamMarkPayload,
    AuditLogEntry, BrandingOut, ConsolidatedOut
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# ---------- Service Dependencies ----------
async def get_tenant_config(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> TenantConfigService:
    return TenantConfigService(db, UUID(tenant_id))

async def get_marking_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AttendanceMarkingService:
    return AttendanceMarkingService(db, UUID(tenant_id))

async def get_reporting_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ReportingService:
    return ReportingService(db, UUID(tenant_id))

async def get_recovery_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> RecoveryService:
    return RecoveryService(db, UUID(tenant_id))

async def get_device_hub(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> DeviceHubService:
    return DeviceHubService(db, UUID(tenant_id))

async def get_shift_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ShiftService:
    return ShiftService(db, UUID(tenant_id))

async def get_leave_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> LeaveService:
    return LeaveService(db, UUID(tenant_id))

async def get_hostel_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> HostelService:
    return HostelService(db, UUID(tenant_id))

async def get_transport_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> TransportService:
    return TransportService(db, UUID(tenant_id))

async def get_analytics_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AdvancedAnalyticsService:
    return AdvancedAnalyticsService(db, UUID(tenant_id))

async def get_integration_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> IntegrationService:
    return IntegrationService(db, UUID(tenant_id))

async def get_compliance_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ComplianceService:
    return ComplianceService(db, UUID(tenant_id))

async def get_branding_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> BrandingService:
    return BrandingService(db, UUID(tenant_id))

# ---------- Core Marking ----------
@router.get("/mark/classes", response_model=list[TeacherClassDTO])
async def teacher_classes(
    teacher_id: Optional[UUID] = None,
    date_: date = Query(default_factory=date.today, alias="date"),
    current_user: User = Depends(get_current_user),
    marking_service: AttendanceMarkingService = Depends(get_marking_service)
):
    tid = teacher_id or UUID(str(current_user.id))
    return await marking_service.get_teacher_classes(tid, date_)

@router.get("/mark/classes/{class_id}/students", response_model=list[StudentMarkingInfo])
async def students_for_marking(
    class_id: UUID,
    date_: date = Query(default_factory=date.today, alias="date"),
    section: Optional[str] = None,
    marking_service: AttendanceMarkingService = Depends(get_marking_service)
):
    return await marking_service.get_students_for_marking(class_id, section, date_)

@router.post("/mark", response_model=BulkMarkResponse,
             dependencies=[Depends(PermissionChecker("attendance:write"))])
async def bulk_mark(
    payload: BulkMarkPayload,
    current_user: User = Depends(get_current_user),
    marking_service: AttendanceMarkingService = Depends(get_marking_service)
):
    data = payload.dict()
    data["source"] = "web"
    return await marking_service.bulk_mark(data, UUID(str(current_user.id)))

@router.post("/punch")
async def employee_punch(
    req: PunchRequest,
    current_user: User = Depends(get_current_user),
    marking_service: AttendanceMarkingService = Depends(get_marking_service)
):
    await marking_service.punch(req.employee_id, req.type, req.timestamp, req.location)
    return {"message": "Punch recorded"}

# ---------- Reports ----------
@router.get("/reports/daily", response_model=DailyReport)
async def daily_report(
    class_id: UUID,
    date_: date = Query(default_factory=date.today, alias="date"),
    reporting_service: ReportingService = Depends(get_reporting_service)
):
    return await reporting_service.daily_class_report(class_id, date_)

@router.get("/reports/student/{student_id}", response_model=list[StudentAttendanceHistory])
async def student_history(
    student_id: UUID,
    from_date: date = Query(...),
    to_date: date = Query(...),
    reporting_service: ReportingService = Depends(get_reporting_service)
):
    return await reporting_service.student_history(student_id, from_date, to_date)

# ---------- Policy ----------
@router.get("/policy", response_model=AttendancePolicyOut)
async def get_policy(config_service: TenantConfigService = Depends(get_tenant_config)):
    policy = await config_service.get_policy()
    if not policy:
        raise HTTPException(404, "Policy not configured")
    return policy

@router.put("/policy", response_model=AttendancePolicyOut)
async def update_policy(
    update: AttendancePolicyUpdate,
    config_service: TenantConfigService = Depends(get_tenant_config)
):
    policy = await config_service.update_config(update.config)
    return policy

# ---------- Recovery ----------
@router.post("/recovery/sessions/generate-proposals", response_model=list)
async def generate_recovery(recovery_service: RecoveryService = Depends(get_recovery_service)):
    proposals = await recovery_service.generate_proposals()
    return proposals

@router.post("/recovery/sessions/{session_id}/confirm")
async def confirm_recovery(session_id: UUID, recovery_service: RecoveryService = Depends(get_recovery_service)):
    await recovery_service.confirm_session(session_id)
    return {"message": "Session confirmed"}

# ---------- Device Hub ----------
@router.post("/device/register", response_model=DeviceOut)
async def register_device(data: DeviceRegister, device_hub: DeviceHubService = Depends(get_device_hub)):
    return await device_hub.register_device(data.dict())

@router.post("/device/event")
async def device_event(event_type: str, payload: dict, device_hub: DeviceHubService = Depends(get_device_hub)):
    return await device_hub.handle_device_event(event_type, payload)

@router.post("/biometric/register", response_model=BiometricTemplateOut)
async def register_biometric(data: BiometricTemplateUpload, device_hub: DeviceHubService = Depends(get_device_hub)):
    return await device_hub.register_template(data.user_id, data.user_type, data.template_data, data.device_type)

@router.post("/qr/scan")
async def qr_scan(data: QRScanRequest, device_hub: DeviceHubService = Depends(get_device_hub)):
    return await device_hub.handle_device_event("qr_scan", data.dict())

@router.post("/ble-nfc/event")
async def ble_nfc_event(data: BLENFCEvent, device_hub: DeviceHubService = Depends(get_device_hub)):
    return await device_hub.handle_device_event("ble_nfc", data.dict())

# ---------- Shifts ----------
@router.post("/shifts/schedule", response_model=List[ShiftOut])
async def create_shifts(data: BulkShiftCreate, shift_service: ShiftService = Depends(get_shift_service)):
    return await shift_service.bulk_create_schedules([s.dict() for s in data.entries])

@router.get("/shifts/employee/{employee_id}", response_model=List[ShiftOut])
async def get_employee_shifts(employee_id: UUID, from_date: date = Query(...), to_date: date = Query(...), shift_service: ShiftService = Depends(get_shift_service)):
    return await shift_service.get_employee_schedules(employee_id, from_date, to_date)

@router.post("/missed-punch/correction")
async def correct_missed_punch(data: MissedPunchCorrection, shift_service: ShiftService = Depends(get_shift_service), current_user: User = Depends(get_current_user)):
    await shift_service.correct_missed_punch(data.dict())
    return {"message": "Correction applied"}

# ---------- Leave ----------
@router.post("/leave/apply", response_model=LeaveOut)
async def apply_leave(data: EmployeeLeaveApply, leave_service: LeaveService = Depends(get_leave_service)):
    return await leave_service.apply_leave(data.dict())

@router.put("/leave/{leave_id}/approve", response_model=LeaveOut)
async def approve_leave(leave_id: UUID, approval: LeaveApproval, leave_service: LeaveService = Depends(get_leave_service), current_user: User = Depends(get_current_user)):
    return await leave_service.approve_leave(leave_id, UUID(str(current_user.id)), approval.status)

@router.get("/leave/my-leaves", response_model=List[LeaveOut])
async def my_leaves(employee_id: UUID = Query(...), leave_service: LeaveService = Depends(get_leave_service)):
    return await leave_service.get_employee_leaves(employee_id)

# ---------- Hostel ----------
@router.post("/hostel/movement")
async def record_hostel_movement(data: HostelMovementEntry, hostel_service: HostelService = Depends(get_hostel_service)):
    await hostel_service.record_movement(data.dict())
    return {"message": "Movement recorded"}

@router.get("/hostel/student/{student_id}/movements")
async def hostel_movements(student_id: UUID, hostel_service: HostelService = Depends(get_hostel_service)):
    return await hostel_service.get_student_movements(student_id)

# ---------- Transport ----------
@router.post("/transport/scan")
async def transport_scan(data: TransportScan, transport_service: TransportService = Depends(get_transport_service)):
    await transport_service.record_scan(data.dict())
    return {"message": "Transport scan recorded"}

# ---------- Analytics ----------
@router.get("/analytics/heatmap")
async def heatmap(class_id: UUID, week_start: date = Query(...), analytics_service: AdvancedAnalyticsService = Depends(get_analytics_service)):
    return await analytics_service.get_heatmap(class_id, week_start)

@router.get("/analytics/compare")
async def compare_analytics(class_ids: str = Query(...), from_date: date = Query(...), to_date: date = Query(...), analytics_service: AdvancedAnalyticsService = Depends(get_analytics_service)):
    ids = [UUID(c.strip()) for c in class_ids.split(",")]
    return await analytics_service.compare_classes(ids, from_date, to_date)

# ---------- Integration ----------
@router.get("/payroll/report", response_model=PayrollReport)
async def payroll_report(employee_id: UUID, from_date: date = Query(...), to_date: date = Query(...), integration_service: IntegrationService = Depends(get_integration_service)):
    return await integration_service.get_employee_payroll_report(employee_id, from_date, to_date)

@router.get("/exam/eligibility/{student_id}", response_model=ExamEligibility)
async def exam_eligibility(student_id: UUID, integration_service: IntegrationService = Depends(get_integration_service)):
    return await integration_service.check_exam_eligibility(student_id)

@router.post("/exam/mark")
async def exam_mark(payload: ExamMarkPayload, integration_service: IntegrationService = Depends(get_integration_service), current_user: User = Depends(get_current_user)):
    count = await integration_service.mark_exam_attendance(payload.exam_id, payload.date, payload.student_ids, UUID(str(current_user.id)))
    return {"marked_count": count}

# ---------- Compliance ----------
@router.post("/compliance/check")
async def compliance_check(compliance_service: ComplianceService = Depends(get_compliance_service)):
    await compliance_service.check_and_enforce()
    return {"status": "completed"}

@router.get("/board-report")
async def board_report(board_type: str = Query("CBSE"), academic_year: str = Query(...), compliance_service: ComplianceService = Depends(get_compliance_service)):
    return await compliance_service.generate_board_report(board_type, academic_year)

# ---------- Audit ----------
@router.get("/audit", response_model=list[AuditLogEntry])
async def audit_log(record_id: Optional[UUID] = None, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    from app.models.attendance_models import AttendanceAuditLog
    query = select(AttendanceAuditLog).where(AttendanceAuditLog.tenant_id == UUID(tenant_id))
    if record_id:
        query = query.where(AttendanceAuditLog.record_id == record_id)
    if from_date:
        query = query.where(AttendanceAuditLog.changed_at >= from_date)
    if to_date:
        query = query.where(AttendanceAuditLog.changed_at <= to_date)
    result = await db.execute(query.order_by(AttendanceAuditLog.changed_at.desc()))
    return result.scalars().all()

# ---------- Branding ----------
@router.get("/branding", response_model=BrandingOut)
async def get_branding(branding_service: BrandingService = Depends(get_branding_service)):
    branding = await branding_service.get_branding()
    if not branding:
        raise HTTPException(404, "Branding not configured")
    return branding

@router.put("/branding", response_model=BrandingOut)
async def update_branding(data: BrandingOut, branding_service: BrandingService = Depends(get_branding_service)):
    return await branding_service.upsert_branding(data.dict(exclude_unset=True))

# ---------- Group Dashboard ----------
@router.get("/group/consolidated", response_model=list[ConsolidatedOut])
async def group_consolidated(group_tenant_id: UUID, db: AsyncSession = Depends(get_db)):
    today = date.today()
    stmt = select(ConsolidatedAttendance).where(
        ConsolidatedAttendance.group_tenant_id == group_tenant_id
    ).where(
        ConsolidatedAttendance.date == today
    )
    result = await db.execute(stmt)
    return result.scalars().all()