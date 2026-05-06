from datetime import date, datetime, timedelta

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.tenant import Tenant
from sqlalchemy import delete, select, update
import asyncio

celery_app = Celery('communication_tasks', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.timezone = 'UTC'

@celery_app.on_after_configure.connect  # type: ignore[misc]
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(300.0, process_scheduled_messages_task, name="process_scheduled")
    sender.add_periodic_task(1800.0, check_escalations_task, name="check_escalations")
    sender.add_periodic_task(crontab(hour=2, minute=0), update_analytics_task, name="update_analytics")
    sender.add_periodic_task(crontab(hour=3, minute=0), archive_old_notifications_task, name="archive_notifications")
    sender.add_periodic_task(crontab(hour=4, minute=0), cleanup_offline_queue_task, name="cleanup_offline")

async def _run_for_all_tenants(task_func):
    async with async_session_factory() as session:
        tenants = (await session.execute(select(Tenant).where(Tenant.is_active == True))).scalars().all()
        for tenant in tenants:
            await task_func(session, tenant.id)

@celery_app.task
def process_scheduled_messages_task():
    async def _task(db, tenant_id):
        from app.modules.communication.services.scheduled_service import ScheduledService
        svc = ScheduledService(db, tenant_id)
        await svc.process_due_schedules()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def check_escalations_task():
    async def _task(db, tenant_id):
        from app.modules.communication.services.escalation_service import EscalationService
        svc = EscalationService(db, tenant_id)
        await svc.check_escalations()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def update_analytics_task():
    async def _task(db, tenant_id):
        from app.modules.communication.services.analytics_service import CommunicationAnalyticsService
        svc = CommunicationAnalyticsService(db, tenant_id)
        # Get all unique recipient_ids from notifications
        from app.models.communication_models import Notification
        users = (await db.execute(select(Notification.recipient_id, Notification.recipient_type).where(Notification.tenant_id == tenant_id).distinct())).all()
        for user_id, user_type in users:
            await svc.update_analytics(user_id, user_type)
    asyncio.run(_run_for_all_tenants(_task))
    
@celery_app.task
def send_fee_reminders_task():
    # Called daily; checks overdue invoices and sends reminders
    async def _task(db, tenant_id):
        from app.models.finance_models import Invoice
        from app.models.communication_models import FeeReminderLog
        from app.modules.communication.services.domain_reminders import DomainReminderService
        svc = DomainReminderService(db, tenant_id)
        overdue = (await db.execute(
            select(Invoice).where(Invoice.tenant_id == tenant_id, Invoice.status.in_(['sent','overdue']), Invoice.due_date < date.today())
        )).scalars().all()
        for inv in overdue:
            # Check last reminder
            last = (await db.execute(
                select(FeeReminderLog).where(FeeReminderLog.invoice_id == inv.id).order_by(FeeReminderLog.sent_at.desc()).limit(1)
            )).scalar_one_or_none()
            stage = (last.reminder_stage + 1) if last else 1
            if stage <= 3:  # max 3 reminders
                await svc.send_fee_reminder(inv.student_id, inv.id, stage)
    asyncio.run(_run_for_all_tenants(_task))
    

@celery_app.task
def archive_old_notifications_task():
    async def _task(db, tenant_id):
        from app.models.communication_models import Notification
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=90)
        stmt = (update(Notification).where(Notification.created_at < cutoff, Notification.tenant_id == tenant_id)
                .values(is_deleted=True))
        await db.execute(stmt)
        await db.commit()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def cleanup_offline_queue_task():
    async def _task(db, tenant_id):
        from app.models.communication_models import OfflineSyncQueue
        cutoff = datetime.utcnow() - timedelta(days=7)
        stmt = delete(OfflineSyncQueue).where(OfflineSyncQueue.created_at < cutoff, OfflineSyncQueue.tenant_id == tenant_id)
        await db.execute(stmt)
        await db.commit()
    asyncio.run(_run_for_all_tenants(_task))