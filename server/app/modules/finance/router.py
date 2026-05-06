from fastapi import APIRouter, Depends, HTTPException, Query, Request
from httpcore import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_tenant
from app.core.permissions import PermissionChecker
from app.models.user import User
from app.modules.finance.services.fee_service import FeeService
from app.modules.finance import schemas

router = APIRouter(prefix="/finance", tags=["Finance"])

async def get_fee_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> FeeService:
    return FeeService(db, UUID(tenant_id))

# Fee Structures
@router.post("/structures", response_model=schemas.FeeStructureOut, dependencies=[Depends(PermissionChecker("fee:create"))])
async def create_fee_structure(data: schemas.FeeStructureCreate, svc: FeeService = Depends(get_fee_service)):
    return await svc.create_fee_structure(data)

@router.get("/structures", response_model=List[schemas.FeeStructureOut], dependencies=[Depends(PermissionChecker("fee:read"))])
async def list_fee_structures(svc: FeeService = Depends(get_fee_service)):
    return await svc.list_fee_structures()

@router.get("/structures/{structure_id}", response_model=schemas.FeeStructureOut, dependencies=[Depends(PermissionChecker("fee:read"))])
async def get_fee_structure(structure_id: UUID, svc: FeeService = Depends(get_fee_service)):
    structure = await svc.get_fee_structure(structure_id)
    if not structure:
        raise HTTPException(404, "Fee structure not found")
    return structure

# Student Fee Accounts
@router.post("/accounts", response_model=schemas.StudentFeeAccountOut, dependencies=[Depends(PermissionChecker("fee:create"))])
async def create_student_account(data: schemas.StudentFeeAccountCreate, svc: FeeService = Depends(get_fee_service)):
    return await svc.create_student_account(data)

@router.get("/accounts/{student_id}", response_model=schemas.StudentFeeAccountOut, dependencies=[Depends(PermissionChecker("fee:read"))])
async def get_student_account(student_id: UUID, svc: FeeService = Depends(get_fee_service)):
    account = await svc.get_student_account(student_id)
    if not account:
        raise HTTPException(404, "Student fee account not found")
    return account

# Invoices
@router.post("/invoices", response_model=schemas.InvoiceOut, dependencies=[Depends(PermissionChecker("fee:create"))])
async def create_invoice(data: schemas.InvoiceCreate, svc: FeeService = Depends(get_fee_service)):
    return await svc.create_invoice(data)

@router.get("/invoices/{invoice_id}", response_model=schemas.InvoiceOut, dependencies=[Depends(PermissionChecker("fee:read"))])
async def get_invoice(invoice_id: UUID, svc: FeeService = Depends(get_fee_service)):
    invoice = await svc.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return invoice

@router.get("/invoices/student/{student_id}", response_model=List[schemas.InvoiceOut], dependencies=[Depends(PermissionChecker("fee:read"))])
async def list_student_invoices(student_id: UUID, svc: FeeService = Depends(get_fee_service)):
    return await svc.list_student_invoices(student_id)

# Payments
@router.post("/payments", response_model=schemas.PaymentOut, dependencies=[Depends(PermissionChecker("fee:collect"))])
async def record_payment(data: schemas.PaymentCreate, svc: FeeService = Depends(get_fee_service)):
    return await svc.record_payment(data)

@router.get("/payments/student/{student_id}", response_model=List[schemas.PaymentOut], dependencies=[Depends(PermissionChecker("fee:read"))])
async def get_student_transactions(student_id: UUID, svc: FeeService = Depends(get_fee_service)):
    return await svc.get_transactions(student_id)

# Discounts
@router.post("/discounts", response_model=schemas.DiscountOut, dependencies=[Depends(PermissionChecker("fee:create"))])
async def apply_discount(data: schemas.DiscountCreate, current_user: User = Depends(get_current_user), svc: FeeService = Depends(get_fee_service)):
    return await svc.apply_discount(data, current_user.id)

# Reports
@router.get("/reports/dues", response_model=List[schemas.DuesReport], dependencies=[Depends(PermissionChecker("fee:read"))])
async def dues_report(class_id: Optional[UUID] = None, svc: FeeService = Depends(get_fee_service)):
    return await svc.get_dues_report(class_id)

@router.get("/reports/ledger", response_model=List[schemas.LedgerEntryOut], dependencies=[Depends(PermissionChecker("finance:read"))])
async def ledger(account: Optional[str] = None, from_date: Optional[date] = None, to_date: Optional[date] = None, svc: FeeService = Depends(get_fee_service)):
    return await svc.get_ledger(account, from_date, to_date)

# Refunds
@router.post("/refunds", response_model=schemas.RefundOut, dependencies=[Depends(PermissionChecker("finance:write"))])
async def request_refund(data: schemas.RefundRequest, svc: FeeService = Depends(get_fee_service)):
    return await svc.request_refund(data)

@router.put("/refunds/{refund_id}/approve", response_model=schemas.RefundOut, dependencies=[Depends(PermissionChecker("finance:approve"))])
async def approve_refund(refund_id: UUID, current_user: User = Depends(get_current_user), svc: FeeService = Depends(get_fee_service)):
    try:
        return await svc.approve_refund(refund_id, current_user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/refunds/{refund_id}/process", response_model=schemas.RefundOut, dependencies=[Depends(PermissionChecker("finance:approve"))])
async def process_refund(refund_id: UUID, svc: FeeService = Depends(get_fee_service)):
    try:
        return await svc.process_refund(refund_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

# Credit Notes
@router.get("/credit-notes/{student_id}", response_model=List[schemas.CreditNoteOut], dependencies=[Depends(PermissionChecker("fee:read"))])
async def list_credit_notes(student_id: UUID, svc: FeeService = Depends(get_fee_service)):
    return await svc.list_credit_notes(student_id)

# Payment Gateway Webhook (public endpoint)
@router.post("/webhook/{gateway}")
async def gateway_webhook(gateway: str, request: Request, svc: FeeService = Depends(get_fee_service)):
    payload = await request.json()
    event_type = payload.get("event", "unknown")
    return await svc.handle_webhook(gateway, event_type, payload)

# Bank Reconciliation
@router.post("/bank/upload", response_model=List[schemas.BankReconciliationOut], dependencies=[Depends(PermissionChecker("finance:reconcile"))])
async def upload_bank_statement(entries: List[dict], svc: FeeService = Depends(get_fee_service)):
    return await svc.upload_bank_statement(entries)

@router.post("/bank/reconcile", dependencies=[Depends(PermissionChecker("finance:reconcile"))])
async def auto_reconcile(svc: FeeService = Depends(get_fee_service)):
    return await svc.auto_reconcile()

# Accounting Periods
@router.post("/periods", response_model=schemas.AccountingPeriodOut, dependencies=[Depends(PermissionChecker("finance:write"))])
async def create_period(data: schemas.AccountingPeriodCreate, svc: FeeService = Depends(get_fee_service)):
    return await svc.create_accounting_period(data)

@router.put("/periods/{period_id}/close", response_model=schemas.AccountingPeriodOut, dependencies=[Depends(PermissionChecker("finance:approve"))])
async def close_period(period_id: UUID, current_user: User = Depends(get_current_user), svc: FeeService = Depends(get_fee_service)):
    try:
        return await svc.close_period(period_id, current_user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))

# Late fee manual trigger (admin)
@router.post("/apply-late-fees", dependencies=[Depends(PermissionChecker("finance:write"))])
async def trigger_late_fees(svc: FeeService = Depends(get_fee_service)):
    await svc.apply_late_fees()
    return {"message": "Late fees applied"}


from app.modules.finance.services.ai_finance_service import AIFinanceService

async def get_ai_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AIFinanceService:
    return AIFinanceService(db, UUID(tenant_id))

ai_router = APIRouter(prefix="/ai", tags=["Finance AI"])

@ai_router.get("/predict-default/{student_id}", response_model=schemas.PaymentRiskOut, dependencies=[Depends(PermissionChecker("fee:read"))])
async def predict_default(student_id: UUID, svc: AIFinanceService = Depends(get_ai_service)):
    return await svc.predict_payment_default(student_id)

@ai_router.post("/train-payment-model", dependencies=[Depends(PermissionChecker("insights:configure"))])
async def train_default_model(svc: AIFinanceService = Depends(get_ai_service)):
    await svc.train_payment_default_model()
    return {"message": "Model trained"}

@ai_router.post("/reminder-timing", response_model=List[schemas.ReminderTimingOut], dependencies=[Depends(PermissionChecker("fee:read"))])
async def reminder_timing(invoice_ids: List[UUID], svc: AIFinanceService = Depends(get_ai_service)):
    return await svc.suggest_reminder_timing(invoice_ids)

@ai_router.post("/detect-anomalies", response_model=List[schemas.AnomalyOut], dependencies=[Depends(PermissionChecker("insights:view"))])
async def detect_anomalies(svc: AIFinanceService = Depends(get_ai_service)):
    return await svc.detect_anomalies()

@ai_router.get("/forecast-revenue", response_model=List[schemas.ForecastOut], dependencies=[Depends(PermissionChecker("insights:view"))])
async def forecast_revenue(months: int = 6, svc: AIFinanceService = Depends(get_ai_service)):
    return await svc.forecast_revenue(months)

@ai_router.post("/train-forecast-model", dependencies=[Depends(PermissionChecker("insights:configure"))])
async def train_forecast_model(svc: AIFinanceService = Depends(get_ai_service)):
    await svc.train_revenue_forecast_model()
    return {"message": "Forecast model trained"}

@ai_router.post("/categorize", dependencies=[Depends(PermissionChecker("finance:write"))])
async def categorize_all(svc: AIFinanceService = Depends(get_ai_service)):
    await svc.categorize_all_transactions()
    return {"message": "Transactions categorized"}

@ai_router.get("/fee-optimization", dependencies=[Depends(PermissionChecker("insights:view"))])
async def fee_optimization(svc: AIFinanceService = Depends(get_ai_service)):
    return await svc.suggest_fee_optimization()

router.include_router(ai_router)   # now the finance router also includes AI endpoints

from app.modules.finance.services.integration_service import FinanceIntegrationService

async def get_integration_service(db: AsyncSession = Depends(get_db),
                                  tenant_id: str = Depends(get_current_active_tenant)) -> FinanceIntegrationService:
    return FinanceIntegrationService(db, UUID(tenant_id))

integration_router = APIRouter(prefix="/integration", tags=["Finance Integration"])

# Parent Portal
@integration_router.get("/student/{student_id}/fee-summary")
async def fee_summary(student_id: UUID, svc: FinanceIntegrationService = Depends(get_integration_service)):
    summary = await svc.get_student_fee_summary(student_id)
    if not summary:
        raise HTTPException(404, "No fee account")
    return summary

@integration_router.post("/student/{student_id}/pay")
async def pay(student_id: UUID, amount: float, payment_mode: str = "online",
              svc: FinanceIntegrationService = Depends(get_integration_service)):
    return await svc.parent_pay(student_id, amount, payment_mode)

# Student Interlock
@integration_router.get("/check-clearance/{student_id}")
async def check_clearance(student_id: UUID, svc: FinanceIntegrationService = Depends(get_integration_service)):
    return await svc.check_fee_clearance(student_id)

@integration_router.post("/set-block/{student_id}")
async def set_block(student_id: UUID, data: schemas.BlockStatusUpdate,
                    svc: FinanceIntegrationService = Depends(get_integration_service)):
    await svc.set_block_rules(student_id, data.block_certificate, data.block_exam)
    return {"message": "Block rules updated"}

# GST
@integration_router.get("/gst-config")
async def get_gst_config(svc: FinanceIntegrationService = Depends(get_integration_service)):
    cfg = await svc.get_gst_config()
    if not cfg:
        raise HTTPException(404, "GST not configured")
    return cfg

@integration_router.put("/gst-config")
async def update_gst_config(data: schemas.GSTConfigCreate,
                            svc: FinanceIntegrationService = Depends(get_integration_service)):
    return await svc.update_gst_config(data.dict())

@integration_router.get("/gst-report")
async def gst_report(from_date: date, to_date: date, svc: FinanceIntegrationService = Depends(get_integration_service)):
    return await svc.generate_gst_report(from_date, to_date)

# Invoice Templates
@integration_router.post("/templates")
async def create_template(data: schemas.InvoiceTemplateCreate,
                          svc: FinanceIntegrationService = Depends(get_integration_service)):
    return await svc.create_invoice_template(data.dict())

@integration_router.get("/invoices/{invoice_id}/pdf")
async def download_pdf(invoice_id: UUID, svc: FinanceIntegrationService = Depends(get_integration_service)):
    try:
        pdf = await svc.render_invoice_pdf(invoice_id)
        return Response(content=pdf, media_type="application/pdf")
    except ValueError as e:
        raise HTTPException(404, str(e))

# Audit Log
@integration_router.get("/audit-log")
async def audit_log(entity_type: str = None, entity_id: UUID = None,
                    from_date: date = None, to_date: date = None,
                    svc: FinanceIntegrationService = Depends(get_integration_service)):
    return await svc.get_audit_log(entity_type, entity_id, from_date, to_date)

router.include_router(integration_router)   # merge into main finance router