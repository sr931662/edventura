import uuid
from sqlalchemy import Column, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import EdVenturaBase
from app.core.database import Base
import sqlalchemy as sa

class FeeStructure(EdVenturaBase):
    __tablename__ = "fee_structures"
    name = Column(String(100), nullable=False)
    academic_year = Column(String(20), nullable=False)
    term = Column(String(20))
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    is_active = Column(Boolean, default=True)

class FeeComponent(EdVenturaBase):
    __tablename__ = "fee_components"
    fee_structure_id = Column(UUID(as_uuid=True), ForeignKey("fee_structures.id"), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    is_optional = Column(Boolean, default=False)

class StudentFeeAccount(EdVenturaBase):
    __tablename__ = "student_fee_accounts"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    fee_structure_id = Column(UUID(as_uuid=True), ForeignKey("fee_structures.id"), nullable=False)
    total_fee = Column(Numeric(10,2), default=0)
    paid_amount = Column(Numeric(10,2), default=0)
    due_amount = Column(Numeric(10,2), default=0)
    installment_plan = Column(JSON, default={})
    late_fee_rule = Column(JSON, default={})
    discounts = Column(Numeric(10,2), default=0)
    block_certificate = Column(Boolean, default=False)
    block_exam = Column(Boolean, default=False)

class Invoice(EdVenturaBase):
    __tablename__ = "invoices"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10,2), nullable=False)
    paid_amount = Column(Numeric(10,2), default=0)
    status = Column(String(20), default='draft')
    template_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text)
    late_fee_applied = Column(Numeric(10,2), default=0)
    last_reminder_sent = Column(DateTime(timezone=True), nullable=True)

class InvoiceItem(EdVenturaBase):
    __tablename__ = "invoice_items"
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)

class Transaction(EdVenturaBase):
    __tablename__ = "transactions"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    amount = Column(Numeric(10,2), nullable=False)
    payment_mode = Column(String(50), nullable=False)
    transaction_reference = Column(String(100))
    paid_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    receipt_number = Column(String(50), unique=True, nullable=False)
    notes = Column(Text)
    category = Column(String(50), nullable=True)

class LedgerEntry(EdVenturaBase):
    __tablename__ = "ledger_entries"
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    account = Column(String(50), nullable=False)
    debit = Column(Numeric(10,2), default=0)
    credit = Column(Numeric(10,2), default=0)
    description = Column(String(200))
    entry_date = Column(Date, server_default=sa.func.current_date())

class Discount(EdVenturaBase):
    __tablename__ = "discounts"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    type = Column(String(50), nullable=False)
    value = Column(Numeric(10,2), nullable=False)
    reason = Column(String(200))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_status = Column(String(20), default='pending')
    
class Refund(EdVenturaBase):
    __tablename__ = "refunds"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    reason = Column(String(200))
    status = Column(String(20), default='requested')
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime(timezone=True))
    credit_note_id = Column(UUID(as_uuid=True), nullable=True)

class CreditNote(EdVenturaBase):
    __tablename__ = "credit_notes"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    reason = Column(String(200))
    issued_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    expiry_date = Column(Date)
    is_used = Column(Boolean, default=False)

class PaymentGatewayLog(EdVenturaBase):
    __tablename__ = "payment_gateway_logs"
    gateway = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, default={})
    reference_id = Column(String(100))
    status = Column(String(20), default='pending')
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)

class BankReconciliationEntry(EdVenturaBase):
    __tablename__ = "bank_reconciliation_entries"
    date = Column(Date, nullable=False)
    description = Column(String(200))
    amount = Column(Numeric(10,2))
    type = Column(String(10))
    reference = Column(String(100))
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    matched = Column(Boolean, default=False)

class AccountingPeriod(EdVenturaBase):
    __tablename__ = "accounting_periods"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    closed = Column(Boolean, default=False)
    closed_at = Column(DateTime(timezone=True))
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
class AIModelMetadata(EdVenturaBase):
    __tablename__ = "ai_model_metadata"
    model_type = Column(String(50), nullable=False)
    model_path = Column(String(255))
    accuracy = Column(Numeric(5,2))
    trained_at = Column(DateTime(timezone=True))
    parameters = Column(JSON, default={})

class PaymentDefaultPrediction(EdVenturaBase):
    __tablename__ = "payment_default_predictions"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    risk_score = Column(Numeric(5,2))
    probability = Column(Numeric(5,2))
    factors = Column(JSON, default={})
    predicted_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class AnomalyLog(EdVenturaBase):
    __tablename__ = "anomaly_logs"
    transaction_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text)
    severity = Column(String(20), default='low')
    detected_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class RevenueForecast(EdVenturaBase):
    __tablename__ = "revenue_forecasts"
    forecast_date = Column(Date, nullable=False)
    predicted_revenue = Column(Numeric(10,2))
    lower_bound = Column(Numeric(10,2))
    upper_bound = Column(Numeric(10,2))

class AutoCategoryRule(EdVenturaBase):
    __tablename__ = "auto_category_rules"
    pattern = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)

class InvoiceTemplate(EdVenturaBase):
    __tablename__ = "invoice_templates"
    name = Column(String(100), nullable=False)
    html_template = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)

class FinanceAuditLog(EdVenturaBase):
    __tablename__ = "finance_audit_log"
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(20), nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    changes = Column(JSON, default={})
    changed_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class GSTConfig(EdVenturaBase):
    __tablename__ = "gst_config"
    tenant_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    gstin = Column(String(20))
    tax_rate_percent = Column(Numeric(5,2), default=0)
    enabled = Column(Boolean, default=False)

