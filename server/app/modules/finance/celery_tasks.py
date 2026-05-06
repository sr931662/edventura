from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.tenant import Tenant
from sqlalchemy import select
import asyncio

from app.modules.finance.services.ai_finance_service import AIFinanceService

celery_app = Celery('finance_tasks', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.timezone = 'UTC'

@celery_app.on_after_configure.connect  # type: ignore[union-attr]
def setup_periodic_tasks(sender, **kwargs):
    # Daily midnight – calculate late fees on overdue invoices
    sender.add_periodic_task(crontab(hour=0, minute=0), calculate_late_fees_task, name="calculate_late_fees")
    # Daily 9 AM – send payment reminders for overdue invoices
    sender.add_periodic_task(crontab(hour=9, minute=0), send_payment_reminders_task, name="send_payment_reminders")

async def _run_for_all_tenants(task_func):
    async with async_session_factory() as session:
        tenants = (await session.execute(select(Tenant).where(Tenant.is_active == True))).scalars().all()
        for tenant in tenants:
            try:
                await task_func(session, tenant.id)
            except Exception as e:
                print(f"Error in tenant {tenant.id}: {e}")

@celery_app.task
def calculate_late_fees_task():
    async def _task(db, tenant_id):
        # Query overdue invoices and apply late fees according to late_fee_rule
        from app.models.finance_models import Invoice, StudentFeeAccount
        from datetime import date
        overdue_invoices = await db.execute(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.status == 'sent',
                Invoice.due_date < date.today()
            )
        )
        for inv in overdue_invoices.scalars():
            account = await db.get(StudentFeeAccount, inv.student_id)
            if account and account.late_fee_rule:
                rule = account.late_fee_rule
                overdue_days = (date.today() - inv.due_date).days
                if rule.get('type') == 'fixed':
                    late_fee = rule.get('value', 0)
                elif rule.get('type') == 'percentage':
                    late_fee = (inv.total_amount * rule.get('value', 0) / 100)
                elif rule.get('type') == 'per_day':
                    late_fee = overdue_days * rule.get('value', 0)
                else:
                    late_fee = 0
                if late_fee > 0:
                    inv.total_amount += late_fee
                    inv.status = 'overdue'
                    account.due_amount += late_fee
                    await db.commit()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def send_payment_reminders_task():
    async def _task(db, tenant_id):
        from app.models.finance_models import Invoice
        from datetime import date
        overdue = await db.execute(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.status.in_(['overdue', 'sent']),
                Invoice.due_date < date.today()
            )
        )
        for inv in overdue.scalars():
            # Publish event for notification service
            from app.modules.attendance.event_publisher import publish_event
            await publish_event("finance_events", {
                "type": "PaymentReminder",
                "tenant_id": str(tenant_id),
                "student_id": str(inv.student_id),
                "invoice_id": str(inv.id),
                "due_date": inv.due_date.isoformat()
            })
    asyncio.run(_run_for_all_tenants(_task))
    
@celery_app.task
def train_payment_default_model_task():
    async def _task(db, tenant_id):
        svc = AIFinanceService(db, tenant_id)
        await svc.train_payment_default_model()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def train_revenue_forecast_model_task():
    async def _task(db, tenant_id):
        svc = AIFinanceService(db, tenant_id)
        await svc.train_revenue_forecast_model()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def detect_anomalies_task():
    async def _task(db, tenant_id):
        svc = AIFinanceService(db, tenant_id)
        await svc.detect_anomalies()
    asyncio.run(_run_for_all_tenants(_task))

@celery_app.task
def categorize_transactions_task():
    async def _task(db, tenant_id):
        svc = AIFinanceService(db, tenant_id)
        await svc.categorize_all_transactions()
    asyncio.run(_run_for_all_tenants(_task))