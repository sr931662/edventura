from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.finance.repository import FinanceRepository
from app.modules.finance import schemas
from app.modules.attendance.event_publisher import publish_event

class FeeService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = FinanceRepository(db, tenant_id)

    # Fee Structures
    async def create_fee_structure(self, data: schemas.FeeStructureCreate) -> schemas.FeeStructureOut:
        structure = await self.repo.create_fee_structure(
            data.dict(exclude={"components"}),
            [c.dict() for c in data.components]
        )
        return self._to_structure_out(structure)

    async def get_fee_structure(self, structure_id: UUID) -> Optional[schemas.FeeStructureOut]:
        structure = await self.repo.get_fee_structure(structure_id)
        if structure:
            return self._to_structure_out(structure)
        return None

    async def list_fee_structures(self) -> List[schemas.FeeStructureOut]:
        structures = await self.repo.list_fee_structures()
        return [self._to_structure_out(s) for s in structures]

    # Student Fee Accounts
    async def create_student_account(self, data: schemas.StudentFeeAccountCreate) -> schemas.StudentFeeAccountOut:
        account = await self.repo.create_student_fee_account(data.dict())
        return schemas.StudentFeeAccountOut.from_orm(account)

    async def get_student_account(self, student_id: UUID) -> Optional[schemas.StudentFeeAccountOut]:
        account = await self.repo.get_student_account(student_id)
        if account:
            return schemas.StudentFeeAccountOut.from_orm(account)
        return None

    # Invoices
    async def create_invoice(self, data: schemas.InvoiceCreate) -> schemas.InvoiceOut:
        invoice = await self.repo.create_invoice(data.dict())
        # Publish event for notification
        await publish_event("finance_events", {
            "type": "InvoiceGenerated",
            "tenant_id": str(self.repo.tenant_id),
            "invoice_id": str(invoice.id),
            "student_id": str(data.student_id)
        })
        return self._to_invoice_out(invoice)

    async def get_invoice(self, invoice_id: UUID) -> Optional[schemas.InvoiceOut]:
        invoice = await self.repo.get_invoice(invoice_id)
        if invoice:
            return self._to_invoice_out(invoice)
        return None

    async def list_student_invoices(self, student_id: UUID) -> List[schemas.InvoiceOut]:
        invoices = await self.repo.list_student_invoices(student_id)
        return [self._to_invoice_out(i) for i in invoices]

    # Payments
    async def record_payment(self, data: schemas.PaymentCreate) -> schemas.PaymentOut:
        payment = await self.repo.record_payment(data.dict())
        # Publish event
        await publish_event("finance_events", {
            "type": "PaymentReceived",
            "tenant_id": str(self.repo.tenant_id),
            "student_id": str(data.student_id),
            "amount": data.amount
        })
        return schemas.PaymentOut.from_orm(payment)

    async def get_transactions(self, student_id: UUID) -> List[schemas.PaymentOut]:
        transactions = await self.repo.get_transactions(student_id)
        return [schemas.PaymentOut.from_orm(t) for t in transactions]

    # Discounts
    async def apply_discount(self, data: schemas.DiscountCreate, approved_by: Optional[UUID] = None) -> schemas.DiscountOut:
        discount_data = data.dict()
        discount_data['approved_by'] = approved_by
        discount = await self.repo.apply_discount(discount_data)
        return schemas.DiscountOut.from_orm(discount)

    # Reports
    async def get_dues_report(self, class_id: Optional[UUID] = None) -> List[schemas.DuesReport]:
        report = await self.repo.get_dues_report(class_id)
        return [schemas.DuesReport(**r) for r in report]

    async def get_ledger(self, account: str = None, from_date: date = None, to_date: date = None) -> List[schemas.LedgerEntryOut]:
        entries = await self.repo.get_ledger(account, from_date, to_date)
        return [schemas.LedgerEntryOut.from_orm(e) for e in entries]

    # Helpers
    def _to_structure_out(self, structure) -> schemas.FeeStructureOut:
        components = []
        # In real, fetch components; but we'll rely on relationship if defined
        # For now, leave components empty; they'll be populated in a full service
        return schemas.FeeStructureOut(
            id=structure.id,
            name=structure.name,
            academic_year=structure.academic_year,
            term=structure.term,
            class_id=structure.class_id,
            is_active=structure.is_active,
            components=[]
        )

    def _to_invoice_out(self, invoice) -> schemas.InvoiceOut:
        items = []  # Similarly, add relationship loading
        return schemas.InvoiceOut(
            id=invoice.id,
            student_id=invoice.student_id,
            invoice_number=invoice.invoice_number,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            total_amount=float(invoice.total_amount),
            paid_amount=float(invoice.paid_amount),
            status=invoice.status,
            notes=invoice.notes,
            items=[]
        )
    # Refunds
    async def request_refund(self, data: schemas.RefundRequest) -> schemas.RefundOut:
        refund = await self.repo.request_refund(data.dict())
        return schemas.RefundOut.from_orm(refund)

    async def approve_refund(self, refund_id: UUID, approved_by: UUID) -> schemas.RefundOut:
        refund = await self.repo.approve_refund(refund_id, approved_by)
        if not refund:
            raise ValueError("Refund not found")
        # Publish event
        await publish_event("finance_events", {
            "type": "RefundApproved",
            "tenant_id": str(self.repo.tenant_id),
            "refund_id": str(refund.id),
            "student_id": str(refund.student_id)
        })
        return schemas.RefundOut.from_orm(refund)

    async def process_refund(self, refund_id: UUID) -> schemas.RefundOut:
        refund = await self.repo.process_refund(refund_id)
        if not refund:
            raise ValueError("Refund cannot be processed")
        return schemas.RefundOut.from_orm(refund)

    # Credit Notes
    async def list_credit_notes(self, student_id: UUID) -> List[schemas.CreditNoteOut]:
        notes = await self.repo.list_credit_notes(student_id)
        return [schemas.CreditNoteOut.from_orm(n) for n in notes]

    # Payment Gateway Webhook
    async def handle_webhook(self, gateway: str, event_type: str, payload: dict):
        log = await self.repo.log_gateway_event({
            "gateway": gateway,
            "event_type": event_type,
            "payload": payload,
            "reference_id": payload.get("reference_id")
        })
        # If payment captured, automatically create transaction
        if event_type == "payment.captured":
            ref = payload.get("reference_id")
            # Try to find an existing invoice for this reference (or create new)
            # Simplified: assume the reference is the student UUID or invoice ID
            # In production, you'd have a mapping table
            # For now, we log and mark for manual reconciliation
            return {"status": "logged", "log_id": str(log.id)}
        return {"status": "logged", "log_id": str(log.id)}

    # Bank Reconciliation
    async def upload_bank_statement(self, entries: List[dict]) -> List[schemas.BankReconciliationOut]:
        records = await self.repo.upload_bank_statement(entries)
        return [schemas.BankReconciliationOut.from_orm(r) for r in records]

    async def auto_reconcile(self) -> dict:
        await self.repo.auto_match_bank_entries()
        return {"message": "Auto‑reconciliation completed"}

    # Accounting Periods
    async def create_accounting_period(self, data: schemas.AccountingPeriodCreate) -> schemas.AccountingPeriodOut:
        period = await self.repo.create_accounting_period(data.dict())
        return schemas.AccountingPeriodOut.from_orm(period)

    async def close_period(self, period_id: UUID, user_id: UUID) -> schemas.AccountingPeriodOut:
        period = await self.repo.close_period(period_id, user_id)
        if not period:
            raise ValueError("Period not found or already closed")
        return schemas.AccountingPeriodOut.from_orm(period)

    # Late Fees (called from Celery)
    async def apply_late_fees(self):
        await self.repo.apply_late_fees()