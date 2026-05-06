from typing import Optional
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.finance_models import (
    StudentFeeAccount, Invoice, InvoiceTemplate, GSTConfig,
    FinanceAuditLog, Transaction
)
from app.modules.attendance.event_publisher import publish_event

class FinanceIntegrationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ---------- Parent Portal ----------
    async def get_student_fee_summary(self, student_id: UUID):
        account = await self.db.get(StudentFeeAccount, student_id)
        if not account:
            return None
        invoices = (await self.db.execute(
            select(Invoice).where(Invoice.student_id == student_id, Invoice.tenant_id == self.tenant_id)
        )).scalars().all()
        return {
            "student_id": student_id,
            "total_fee": float(account.total_fee),
            "paid_amount": float(account.paid_amount),
            "due_amount": float(account.due_amount),
            "next_due_date": min((inv.due_date for inv in invoices if inv.status != 'paid'), default=None)
        }

    async def parent_pay(self, student_id: UUID, amount: float, payment_mode: str):
        from app.modules.finance.repository import FinanceRepository
        repo = FinanceRepository(self.db, self.tenant_id)
        tx = await repo.record_payment({
            "student_id": student_id,
            "amount": amount,
            "payment_mode": payment_mode,
            "notes": "Parent portal payment"
        })
        await publish_event("finance_events", {
            "type": "ParentPaymentReceived",
            "tenant_id": str(self.tenant_id),
            "student_id": str(student_id),
            "amount": amount
        })
        return {"transaction_id": str(tx.id), "receipt_number": tx.receipt_number}

    # ---------- Student Module Interlock ----------
    async def check_fee_clearance(self, student_id: UUID) -> dict:
        account = await self.db.get(StudentFeeAccount, student_id)
        if not account:
            return {"clear": True}
        return {
            "clear": account.due_amount <= 0,
            "due_amount": float(account.due_amount),
            "block_certificate": account.block_certificate,
            "block_exam": account.block_exam
        }

    async def set_block_rules(self, student_id: UUID, block_cert: bool, block_ex: bool):
        account = await self.db.get(StudentFeeAccount, student_id)
        if account:
            account.block_certificate = block_cert
            account.block_exam = block_ex
            await self.db.commit()

    # ---------- GST / Tax ----------
    async def get_gst_config(self) -> Optional[GSTConfig]:
        stmt = select(GSTConfig).where(GSTConfig.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_gst_config(self, data: dict) -> GSTConfig:
        config = await self.get_gst_config()
        if config:
            for k, v in data.items():
                setattr(config, k, v)
        else:
            config = GSTConfig(tenant_id=self.tenant_id, **data)
            self.db.add(config)
        await self.db.commit()
        return config

    async def generate_gst_report(self, from_date: date, to_date: date) -> dict:
        total_revenue = (await self.db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.tenant_id == self.tenant_id,
                Transaction.paid_at >= from_date,
                Transaction.paid_at <= to_date
            )
        )).scalar() or 0
        total_revenue = float(total_revenue)
        gst = await self.get_gst_config()
        tax_rate = float(gst.tax_rate_percent) if gst and gst.enabled else 0.0
        tax_amount = total_revenue * tax_rate / (100 + tax_rate) if tax_rate > 0 else 0.0
        return {
            "total_revenue": total_revenue,
            "taxable_amount": total_revenue - tax_amount,
            "tax_rate": tax_rate,
            "tax_amount": round(tax_amount, 2)
        }

    # ---------- White‑label Invoicing ----------
    async def create_invoice_template(self, data: dict) -> InvoiceTemplate:
        template = InvoiceTemplate(tenant_id=self.tenant_id, **data)
        self.db.add(template)
        await self.db.commit()
        return template

    async def get_invoice_template(self, template_id: UUID) -> Optional[InvoiceTemplate]:
        return await self.db.get(InvoiceTemplate, template_id)

    async def render_invoice_pdf(self, invoice_id: UUID) -> bytes:
        invoice = await self.db.get(Invoice, invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        template = (await self.db.execute(
            select(InvoiceTemplate).where(
                InvoiceTemplate.tenant_id == self.tenant_id,
                InvoiceTemplate.is_default == True
            )
        )).scalar_one_or_none()
        if not template:
            raise ValueError("No default invoice template configured")
        html = template.html_template.replace("{{invoice_number}}", invoice.invoice_number)
        html = html.replace("{{total_amount}}", str(invoice.total_amount))
        html = html.replace("{{due_date}}", str(invoice.due_date))
        import weasyprint
        return weasyprint.HTML(string=html).write_pdf()

    # ---------- Audit Log ----------
    async def get_audit_log(self, entity_type: str = None, entity_id: UUID = None,
                            from_date: date = None, to_date: date = None) -> list:
        stmt = select(FinanceAuditLog).where(FinanceAuditLog.tenant_id == self.tenant_id)
        if entity_type:
            stmt = stmt.where(FinanceAuditLog.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(FinanceAuditLog.entity_id == entity_id)
        if from_date:
            stmt = stmt.where(FinanceAuditLog.changed_at >= from_date)
        if to_date:
            stmt = stmt.where(FinanceAuditLog.changed_at <= to_date)
        result = await self.db.execute(stmt.order_by(FinanceAuditLog.changed_at.desc()))
        return result.scalars().all()