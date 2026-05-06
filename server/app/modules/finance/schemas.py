from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class FeeComponentCreate(BaseModel):
    name: str
    amount: float
    is_optional: bool = False

class FeeComponentOut(BaseModel):
    id: UUID
    name: str
    amount: float
    is_optional: bool
    class Config:
        from_attributes = True

class FeeStructureCreate(BaseModel):
    name: str
    academic_year: str
    term: Optional[str] = None
    class_id: Optional[UUID] = None
    components: List[FeeComponentCreate] = []

class FeeStructureOut(BaseModel):
    id: UUID
    name: str
    academic_year: str
    term: Optional[str]
    class_id: Optional[UUID]
    is_active: bool
    components: List[FeeComponentOut] = []
    class Config:
        from_attributes = True

class StudentFeeAccountCreate(BaseModel):
    student_id: UUID
    fee_structure_id: UUID
    installment_plan: Optional[dict] = None
    late_fee_rule: Optional[dict] = None
    discounts: float = 0.0

class StudentFeeAccountOut(BaseModel):
    id: UUID
    student_id: UUID
    fee_structure_id: UUID
    total_fee: float
    paid_amount: float
    due_amount: float
    installment_plan: dict
    late_fee_rule: dict
    discounts: float
    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    student_id: UUID
    due_date: date
    items: List[FeeComponentCreate]
    notes: Optional[str] = None

class InvoiceOut(BaseModel):
    id: UUID
    student_id: UUID
    invoice_number: str
    issue_date: date
    due_date: date
    total_amount: float
    paid_amount: float
    status: str
    notes: Optional[str]
    items: List[FeeComponentOut] = []
    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    student_id: UUID
    invoice_id: Optional[UUID] = None
    amount: float
    payment_mode: str = Field(..., pattern="^(cash|upi|card|bank_transfer|online)$")
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None

class PaymentOut(BaseModel):
    id: UUID
    student_id: UUID
    invoice_id: Optional[UUID]
    amount: float
    payment_mode: str
    transaction_reference: Optional[str]
    receipt_number: str
    paid_at: datetime
    notes: Optional[str]
    class Config:
        from_attributes = True

class LedgerEntryOut(BaseModel):
    id: UUID
    account: str
    debit: float
    credit: float
    description: Optional[str]
    entry_date: date

class DuesReport(BaseModel):
    student_id: UUID
    student_name: str
    total_fee: float
    paid_amount: float
    due_amount: float
    overdue_days: int

class DiscountCreate(BaseModel):
    student_id: UUID
    type: str
    value: float
    reason: Optional[str] = None

class DiscountOut(BaseModel):
    id: UUID
    student_id: UUID
    type: str
    value: float
    reason: Optional[str]
    approval_status: str
    class Config:
        from_attributes = True
        
class RefundRequest(BaseModel):
    student_id: UUID
    transaction_id: UUID
    amount: float
    reason: Optional[str] = None

class RefundOut(BaseModel):
    id: UUID
    student_id: UUID
    transaction_id: UUID
    amount: float
    reason: Optional[str]
    status: str
    credit_note_id: Optional[UUID]
    class Config:
        from_attributes = True

class CreditNoteOut(BaseModel):
    id: UUID
    student_id: UUID
    amount: float
    reason: Optional[str]
    issued_at: datetime
    expiry_date: Optional[date]
    is_used: bool
    class Config:
        from_attributes = True

class BankReconciliationOut(BaseModel):
    id: UUID
    date: date
    description: Optional[str]
    amount: float
    type: str
    reference: Optional[str]
    matched: bool
    class Config:
        from_attributes = True

class AccountingPeriodCreate(BaseModel):
    start_date: date
    end_date: date

class AccountingPeriodOut(BaseModel):
    id: UUID
    start_date: date
    end_date: date
    closed: bool
    closed_at: Optional[datetime]
    class Config:
        from_attributes = True

class PaymentRiskOut(BaseModel):
    student_id: UUID
    risk_score: float
    probability: float
    factors: dict

class AnomalyOut(BaseModel):
    id: UUID
    transaction_id: Optional[UUID]
    description: str
    severity: str
    detected_at: datetime

class ForecastOut(BaseModel):
    date: date
    predicted_revenue: float
    lower_bound: float
    upper_bound: float

class ReminderTimingOut(BaseModel):
    invoice_id: UUID
    optimal_time: str   # "HH:MM"
    expected_response_rate: float

class FeeOptimizationSuggestion(BaseModel):
    class_id: Optional[UUID]
    current_fee: float
    suggested_fee: float
    confidence: float
    
class GSTConfigCreate(BaseModel):
    gstin: Optional[str] = None
    tax_rate_percent: float = 0.0
    enabled: bool = False

class GSTConfigOut(BaseModel):
    id: UUID
    gstin: Optional[str]
    tax_rate_percent: float
    enabled: bool

class InvoiceTemplateCreate(BaseModel):
    name: str
    html_template: str
    is_default: bool = False

class InvoiceTemplateOut(BaseModel):
    id: UUID
    name: str
    html_template: str
    is_default: bool

class FeeClearanceOut(BaseModel):
    clear: bool
    due_amount: float
    block_certificate: bool
    block_exam: bool

class BlockStatusUpdate(BaseModel):
    block_certificate: bool = False
    block_exam: bool = False