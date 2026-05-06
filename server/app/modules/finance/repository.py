from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from app.models.finance_models import (
    AccountingPeriod, BankReconciliationEntry, CreditNote, FeeStructure, FeeComponent, PaymentGatewayLog, Refund, StudentFeeAccount, Invoice,
    InvoiceItem, Transaction, LedgerEntry, Discount
)
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import uuid as uuid_mod

class FinanceRepository:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ---------- Fee Structures ----------
    async def create_fee_structure(self, data: dict, components: list[dict]) -> FeeStructure:
        structure = FeeStructure(tenant_id=self.tenant_id, **data)
        self.db.add(structure)
        for comp in components:
            self.db.add(FeeComponent(tenant_id=self.tenant_id, fee_structure_id=structure.id, **comp))
        await self.db.commit()
        return structure

    async def get_fee_structure(self, structure_id: UUID) -> Optional[FeeStructure]:
        stmt = select(FeeStructure).where(FeeStructure.id == structure_id, FeeStructure.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_fee_structures(self) -> List[FeeStructure]:
        stmt = select(FeeStructure).where(FeeStructure.tenant_id == self.tenant_id, FeeStructure.is_deleted == False)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Student Fee Accounts ----------
    async def create_student_fee_account(self, data: dict) -> StudentFeeAccount:
        # Calculate total fee from components of the fee structure
        structure = await self.get_fee_structure(data['fee_structure_id'])
        if not structure:
            raise ValueError("Fee structure not found")
        comps = await self.db.execute(select(func.sum(FeeComponent.amount)).where(FeeComponent.fee_structure_id == structure.id))
        total = comps.scalar() or 0
        account = StudentFeeAccount(
            tenant_id=self.tenant_id,
            student_id=data['student_id'],
            fee_structure_id=data['fee_structure_id'],
            total_fee=total,
            due_amount=total - data.get('discounts', 0),
            installment_plan=data.get('installment_plan', {}),
            late_fee_rule=data.get('late_fee_rule', {}),
            discounts=data.get('discounts', 0)
        )
        self.db.add(account)
        await self.db.commit()
        return account

    async def get_student_account(self, student_id: UUID) -> Optional[StudentFeeAccount]:
        stmt = select(StudentFeeAccount).where(
            StudentFeeAccount.student_id == student_id,
            StudentFeeAccount.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- Invoices ----------
    async def create_invoice(self, data: dict) -> Invoice:
        invoice_number = f"INV-{self.tenant_id}-{uuid_mod.uuid4().hex[:8]}"
        total = sum(item['amount'] for item in data['items'])
        invoice = Invoice(
            tenant_id=self.tenant_id,
            student_id=data['student_id'],
            invoice_number=invoice_number,
            issue_date=date.today(),
            due_date=data['due_date'],
            total_amount=total,
            status='draft',
            notes=data.get('notes')
        )
        self.db.add(invoice)
        for item in data['items']:
            self.db.add(InvoiceItem(tenant_id=self.tenant_id, invoice_id=invoice.id, **item))
        await self.db.commit()
        return invoice

    async def get_invoice(self, invoice_id: UUID) -> Optional[Invoice]:
        stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_student_invoices(self, student_id: UUID) -> List[Invoice]:
        stmt = select(Invoice).where(Invoice.student_id == student_id, Invoice.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Transactions & Receipts ----------
    async def record_payment(self, data: dict) -> Transaction:
        receipt_number = f"RCP-{self.tenant_id}-{uuid_mod.uuid4().hex[:8]}"
        transaction = Transaction(
            tenant_id=self.tenant_id,
            student_id=data['student_id'],
            invoice_id=data.get('invoice_id'),
            amount=data['amount'],
            payment_mode=data['payment_mode'],
            transaction_reference=data.get('transaction_reference'),
            receipt_number=receipt_number,
            notes=data.get('notes')
        )
        self.db.add(transaction)

        # Update invoice paid amount
        if data.get('invoice_id'):
            invoice = await self.get_invoice(data['invoice_id'])
            if invoice:
                invoice.paid_amount = (invoice.paid_amount or 0) + data['amount']
                invoice.status = 'paid' if invoice.paid_amount >= invoice.total_amount else 'sent'

        # Update student fee account
        account = await self.get_student_account(data['student_id'])
        if account:
            account.paid_amount = (account.paid_amount or 0) + data['amount']
            account.due_amount = (account.total_fee or 0) - account.paid_amount - (account.discounts or 0)

        # Auto ledger entry (double-entry)
        self.db.add(LedgerEntry(
            tenant_id=self.tenant_id,
            transaction_id=transaction.id,
            account='Cash/Bank',
            debit=data['amount'],
            credit=0,
            description=f'Fee received - {receipt_number}'
        ))
        self.db.add(LedgerEntry(
            tenant_id=self.tenant_id,
            transaction_id=transaction.id,
            account='Fee Income',
            debit=0,
            credit=data['amount'],
            description=f'Fee collection - {receipt_number}'
        ))

        await self.db.commit()
        return transaction

    async def get_transactions(self, student_id: UUID) -> List[Transaction]:
        stmt = select(Transaction).where(Transaction.student_id == student_id, Transaction.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Discounts ----------
    async def apply_discount(self, data: dict) -> Discount:
        discount = Discount(tenant_id=self.tenant_id, **data)
        self.db.add(discount)
        if discount.approval_status == 'approved':
            account = await self.get_student_account(data['student_id'])
            if account:
                account.discounts = (account.discounts or 0) + data['value']
                account.due_amount = (account.total_fee or 0) - (account.paid_amount or 0) - account.discounts
        await self.db.commit()
        return discount

    # ---------- Reports ----------
    async def get_dues_report(self, class_id: Optional[UUID] = None) -> List[dict]:
        from app.models.student import Student
        stmt = select(StudentFeeAccount).where(StudentFeeAccount.tenant_id == self.tenant_id)
        if class_id:
            # join with students to filter by class
            stmt = stmt.join(Student, StudentFeeAccount.student_id == Student.id).where(Student.class_id == class_id)
        result = await self.db.execute(stmt)
        accounts = result.scalars().all()
        report = []
        for acc in accounts:
            student = await self.db.get(Student, acc.student_id)
            overdue_days = (date.today() - (await self._get_latest_invoice_due_date(acc.student_id))).days if acc.due_amount > 0 else 0
            report.append({
                "student_id": acc.student_id,
                "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
                "total_fee": float(acc.total_fee),
                "paid_amount": float(acc.paid_amount),
                "due_amount": float(acc.due_amount),
                "overdue_days": max(0, overdue_days)
            })
        return report

    async def _get_latest_invoice_due_date(self, student_id: UUID) -> date:
        stmt = select(Invoice.due_date).where(Invoice.student_id == student_id).order_by(Invoice.due_date.desc()).limit(1)
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        return row if row else date.today()

    async def get_ledger(self, account: Optional[str] = None, from_date: Optional[date] = None, to_date: Optional[date] = None) -> List[LedgerEntry]:
        stmt = select(LedgerEntry).where(LedgerEntry.tenant_id == self.tenant_id)
        if account:
            stmt = stmt.where(LedgerEntry.account == account)
        if from_date:
            stmt = stmt.where(LedgerEntry.entry_date >= from_date)
        if to_date:
            stmt = stmt.where(LedgerEntry.entry_date <= to_date)
        result = await self.db.execute(stmt.order_by(LedgerEntry.entry_date))
        return list(result.scalars().all())

    
    # ---------- Refunds ----------
    async def request_refund(self, data: dict) -> Refund:
        refund = Refund(tenant_id=self.tenant_id, **data)
        self.db.add(refund)
        await self.db.commit()
        return refund

    async def approve_refund(self, refund_id: UUID, approved_by: UUID) -> Optional[Refund]:
        refund = await self.db.get(Refund, refund_id)
        if not refund or refund.tenant_id != self.tenant_id:
            return None
        refund.status = 'approved'
        refund.approved_by = approved_by
        # Create credit note
        credit_note = CreditNote(
            tenant_id=self.tenant_id,
            student_id=refund.student_id,
            amount=refund.amount,
            reason=f"Refund for transaction {refund.transaction_id}"
        )
        self.db.add(credit_note)
        await self.db.flush()
        refund.credit_note_id = credit_note.id
        await self.db.commit()
        return refund

    async def process_refund(self, refund_id: UUID) -> Optional[Refund]:
        refund = await self.db.get(Refund, refund_id)
        if not refund or refund.status != 'approved':
            return None
        refund.status = 'processed'
        refund.processed_at = datetime.now()
        # Reverse the original payment (simplified: create a reversal entry)
        # In real, call gateway API. Here we just log.
        await self.db.commit()
        return refund

    # ---------- Credit Notes ----------
    async def list_credit_notes(self, student_id: UUID) -> List[CreditNote]:
        stmt = select(CreditNote).where(CreditNote.student_id == student_id, CreditNote.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Payment Gateway Logs ----------
    async def log_gateway_event(self, data: dict) -> PaymentGatewayLog:
        log = PaymentGatewayLog(tenant_id=self.tenant_id, **data)
        self.db.add(log)
        await self.db.commit()
        return log

    async def reconcile_gateway_event(self, log_id: UUID, transaction_id: UUID):
        log = await self.db.get(PaymentGatewayLog, log_id)
        if log:
            log.status = 'matched'
            log.transaction_id = transaction_id
            await self.db.commit()

    # ---------- Bank Reconciliation ----------
    async def upload_bank_statement(self, entries: List[dict]) -> List[BankReconciliationEntry]:
        records = []
        for entry in entries:
            rec = BankReconciliationEntry(tenant_id=self.tenant_id, **entry)
            self.db.add(rec)
            records.append(rec)
        await self.db.commit()
        return records

    async def auto_match_bank_entries(self):
        # Match bank entries to transactions by reference or amount+date
        bank_entries = await self.db.execute(
            select(BankReconciliationEntry).where(
                BankReconciliationEntry.tenant_id == self.tenant_id,
                BankReconciliationEntry.matched == False
            )
        )
        for be in bank_entries.scalars():
            # Try to find a matching transaction
            stmt = select(Transaction).where(
                Transaction.tenant_id == self.tenant_id,
                Transaction.amount == be.amount,
                Transaction.transaction_reference == be.reference
            ).limit(1)
            tx = (await self.db.execute(stmt)).scalar_one_or_none()
            if tx:
                be.transaction_id = tx.id
                be.matched = True
            else:
                # try by date and amount only
                stmt = select(Transaction).where(
                    Transaction.tenant_id == self.tenant_id,
                    Transaction.amount == be.amount,
                    func.date(Transaction.paid_at) == be.date
                ).limit(1)
                tx = (await self.db.execute(stmt)).scalar_one_or_none()
                if tx:
                    be.transaction_id = tx.id
                    be.matched = True
        await self.db.commit()

    # ---------- Accounting Periods ----------
    async def create_accounting_period(self, data: dict) -> AccountingPeriod:
        period = AccountingPeriod(tenant_id=self.tenant_id, **data)
        self.db.add(period)
        await self.db.commit()
        return period

    async def close_period(self, period_id: UUID, closed_by: UUID) -> Optional[AccountingPeriod]:
        period = await self.db.get(AccountingPeriod, period_id)
        if not period or period.closed:
            return None
        period.closed = True
        period.closed_at = datetime.now()
        period.closed_by = closed_by
        await self.db.commit()
        return period

    # ---------- Installment & Late Fee Helpers ----------
    async def apply_late_fees(self):
        # This will be called by Celery task; iterate overdue invoices and update
        today = date.today()
        stmt = select(Invoice).where(
            Invoice.tenant_id == self.tenant_id,
            Invoice.status.in_(['sent', 'overdue']),
            Invoice.due_date < today
        )
        invoices = (await self.db.execute(stmt)).scalars().all()
        for inv in invoices:
            account = await self.db.get(StudentFeeAccount, inv.student_id)
            if account and account.late_fee_rule:
                rule = account.late_fee_rule
                overdue_days = (today - inv.due_date).days
                late_fee = 0
                if rule.get('type') == 'fixed':
                    late_fee = float(rule.get('value', 0))
                elif rule.get('type') == 'percentage':
                    late_fee = float(inv.total_amount) * float(rule.get('value', 0)) / 100
                elif rule.get('type') == 'per_day':
                    late_fee = overdue_days * float(rule.get('value', 0))
                if late_fee > 0 and late_fee != float(inv.late_fee_applied or 0):
                    # adjust invoice total and student account
                    inv.total_amount = float(inv.total_amount) + late_fee - float(inv.late_fee_applied or 0)
                    inv.late_fee_applied = late_fee
                    inv.status = 'overdue'
                    account.due_amount = float(account.due_amount) + late_fee - float(inv.late_fee_applied or 0)
            await self.db.commit()