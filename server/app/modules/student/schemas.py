from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class GuardianCreate(BaseModel):
    full_name: str
    relation: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_primary: bool = False

class GuardianOut(BaseModel):
    id: UUID
    full_name: str
    relation: str
    phone: Optional[str]
    email: Optional[str]
    is_primary: bool

    class Config:
        from_attributes = True

class StudentCreate(BaseModel):
    # Required
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    date_of_birth: date
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    admission_date: date
    # Optional
    middle_name: Optional[str] = None
    blood_group: Optional[str] = None
    medical_notes: Optional[str] = None
    # Class assignment
    class_id: Optional[UUID] = None   # foreign key to Class (future)
    section: Optional[str] = None
    roll_number: Optional[str] = None
    # Contact
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    # Guardian
    guardians: Optional[List[GuardianCreate]] = []

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    medical_notes: Optional[str] = None
    class_id: Optional[UUID] = None
    section: Optional[str] = None
    roll_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_active: Optional[bool] = None

class StudentOut(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str]
    full_name: str   # computed
    date_of_birth: date
    gender: str
    admission_date: date
    blood_group: Optional[str]
    medical_notes: Optional[str]
    class_id: Optional[UUID]
    section: Optional[str]
    roll_number: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    is_active: bool
    exit_date: Optional[date]
    exit_reason: Optional[str]
    guardians: List[GuardianOut] = []

    class Config:
        from_attributes = True

class BulkPromoteRequest(BaseModel):
    from_class_id: UUID
    to_class_id: UUID
    section: Optional[str] = None

class BulkTransferRequest(BaseModel):
    student_ids: List[UUID]
    target_class_id: UUID
    target_section: Optional[str] = None