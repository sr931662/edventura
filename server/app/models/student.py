from sqlalchemy import Column, String, Date, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import EdVenturaBase
import uuid

class Student(EdVenturaBase):
    __tablename__ = "students"

    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    admission_date = Column(Date, nullable=False)
    exit_date = Column(Date)
    exit_reason = Column(String(255))
    blood_group = Column(String(5))
    medical_notes = Column(Text)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    section = Column(String(20))
    roll_number = Column(String(20))
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(20))
    is_active = Column(Boolean, default=True)

    # Relationships
    guardians = relationship("Guardian", back_populates="student", cascade="all, delete-orphan")

class Guardian(EdVenturaBase):
    __tablename__ = "guardians"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    relation = Column(String(50), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    is_primary = Column(Boolean, default=False)

    student = relationship("Student", back_populates="guardians")