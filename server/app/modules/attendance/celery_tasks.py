from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.tenant import Tenant
from app.models.student import Student
from app.models.class_ import Class as ClassModel
from sqlalchemy import select
import asyncio
from datetime import date, timedelta

celery_app = Celery(
    'attendance_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(timezone='UTC')

# ---------------------------------------------------------------
# Periodic tasks
# ---------------------------------------------------------------
@celery_app.on_after_configure.connect  # type: ignore[union-attr]
def setup_periodic_tasks(sender, **kwargs):
    # Daily 6 AM – Pre‑populate attendance records from timetable
    sender.add_periodic_task(
        crontab(hour=6, minute=0),
        pre_populate_attendance_task,
        name="pre_populate_attendance"
    )
    # Daily 10 PM – Compute daily attendance percentages
    sender.add_periodic_task(
        crontab(hour=22, minute=0),
        compute_daily_attendance_task,
        name="compute_daily_attendance"
    )
    # Daily 9 PM – Detect missed employee punches
    sender.add_periodic_task(
        crontab(hour=21, minute=0),
        detect_missed_punches_task,
        name="detect_missed_punches"
    )
    # Daily 21:30 – Night roll‑call for hostels
    sender.add_periodic_task(
        crontab(hour=21, minute=30),
        night_roll_call_task,
        name="night_roll_call"
    )
    # Daily 11 PM – Recalculate risk scores
    sender.add_periodic_task(
        crontab(hour=23, minute=0),
        risk_score_recalculation_task,
        name="risk_score_recalculation"
    )
    # Daily 8 AM – Compliance check & warnings
    sender.add_periodic_task(
        crontab(hour=8, minute=0),
        compliance_check_task,
        name="compliance_check"
    )
    # Daily 8 PM – Parent digest
    sender.add_periodic_task(
        crontab(hour=20, minute=0),
        daily_digest_task,
        name="daily_digest"
    )
    # Weekly Sunday 2 AM – Retrain forecast models
    sender.add_periodic_task(
        crontab(hour=2, minute=0, day_of_week='sunday'),
        forecast_retraining_task,
        name="forecast_retraining"
    )
    # Weekly Sunday 3 AM – Heatmap aggregation
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week='sunday'),
        heatmap_aggregation_task,
        name="heatmap_aggregation"
    )
    # Every 15 minutes – refresh consolidated dashboards for chain owners
    sender.add_periodic_task(
        900.0,
        refresh_consolidated_dashboard_task,
        name="refresh_consolidated_dashboard"
    )

# ---------------------------------------------------------------
# Helper: run async task for all active tenants
# ---------------------------------------------------------------
async def _run_for_all_tenants(task_func):
    async with async_session_factory() as session:
        tenants = (await session.execute(
            select(Tenant).where(Tenant.is_active == True)
        )).scalars().all()
        for tenant in tenants:
            try:
                await task_func(session, tenant.id)
            except Exception as e:
                # log error per tenant
                print(f"Error in tenant {tenant.id}: {e}")

# ---------------------------------------------------------------
# Task implementations
# ---------------------------------------------------------------
@celery_app.task
def pre_populate_attendance_task():
    async def _task(db, tenant_id):
        # For real implementation, call timetable service to get today's schedule
        # and insert unmarked records for each class/period.
        # Here we just log.
        pass
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def compute_daily_attendance_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.computation import AttendanceComputationService
        svc = AttendanceComputationService(db, tenant_id)
        await svc.compute_daily(date.today())
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def detect_missed_punches_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.shift_service import ShiftService
        svc = ShiftService(db, tenant_id)
        await svc.detect_missed_punches(date.today())
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def night_roll_call_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.hostel_service import HostelService
        svc = HostelService(db, tenant_id)
        await svc.night_roll_call()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def risk_score_recalculation_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.ai.risk_engine import RiskEngine
        engine = RiskEngine(db, tenant_id)
        students = (await db.execute(
            select(Student).where(Student.tenant_id == tenant_id, Student.is_active == True)
        )).scalars().all()
        for s in students:
            await engine.compute_risk(s.id)
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def compliance_check_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.compliance_service import ComplianceService
        svc = ComplianceService(db, tenant_id)
        await svc.check_and_enforce()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def daily_digest_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.integration_service import IntegrationService
        svc = IntegrationService(db, tenant_id)
        await svc.send_parent_digest(date.today())
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def forecast_retraining_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.ai.forecast_service import ForecastService
        svc = ForecastService(db, tenant_id)
        # get all classes for this tenant and train
        classes = (await db.execute(
            select(ClassModel).where(ClassModel.tenant_id == tenant_id)
        )).scalars().all()
        for cls in classes:
            await svc.train_class_model(cls.id)
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def heatmap_aggregation_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.advanced_analytics import AdvancedAnalyticsService
        svc = AdvancedAnalyticsService(db, tenant_id)
        week_start = date.today() - timedelta(days=date.today().weekday())
        classes = (await db.execute(
            select(ClassModel).where(ClassModel.tenant_id == tenant_id)
        )).scalars().all()
        for cls in classes:
            await svc.aggregate_heatmap(cls.id, week_start)
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def refresh_consolidated_dashboard_task():
    async def _task(db, tenant_id):
        from app.modules.attendance.services.branding_service import BrandingService
        svc = BrandingService(db, tenant_id)
        # In a real multi‑tenant setup, group memberships would be queried.
        # For now, we skip.
        pass
    asyncio.run(_run_for_all_tenants(_task))