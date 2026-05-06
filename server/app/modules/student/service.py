from uuid import UUID
from datetime import date
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.student.repository import StudentRepository
from app.modules.student import schemas

class StudentService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = StudentRepository(db, tenant_id)

    async def create_student(self, data: schemas.StudentCreate) -> schemas.StudentOut:
        student_dict = data.dict(exclude={"guardians"})
        guardians = data.guardians

        student = await self.repo.create(
            student_dict,
            [g.dict() for g in guardians] if guardians else None
        )

        # Force async-safe relationship loading
        await self.repo.db.refresh(student, attribute_names=["guardians"])

        return self._to_out(student)

    async def get_student(self, student_id: UUID) -> Optional[schemas.StudentOut]:
        student = await self.repo.get_by_id(student_id)
        if student:
            return self._to_out(student)
        return None

    async def list_students(self, class_id: Optional[UUID] = None, is_active: bool = True, skip: int = 0, limit: int = 100):
        students = await self.repo.list_students(class_id, is_active, skip, limit)
        return [self._to_out(s) for s in students]

    async def update_student(self, student_id: UUID, data: schemas.StudentUpdate):
        update_data = data.dict(exclude_unset=True)
        student = await self.repo.update(student_id, update_data)
        if student:
            return self._to_out(student)
        return None

    async def exit_student(self, student_id: UUID, reason: str, exit_date: Optional[date] = None):
        if exit_date is None:
            exit_date = date.today()
        student = await self.repo.exit_student(student_id, reason, exit_date)
        if student:
            return self._to_out(student)
        return None

    async def bulk_promote(self, from_class_id: UUID, to_class_id: UUID, section: Optional[str] = None):
        count = await self.repo.bulk_promote(from_class_id, to_class_id, section)
        return count

    def _to_out(self, student) -> schemas.StudentOut:
        first = student.first_name
        middle = student.middle_name or ""
        last = student.last_name

        computed_full_name = f"{first} {middle} {last}".strip().replace("  ", " ")

        guardians = getattr(student, "guardians", []) or []

        return schemas.StudentOut(
            id=student.id,
            first_name=student.first_name,
            last_name=student.last_name,
            middle_name=student.middle_name,
            full_name=computed_full_name,
            date_of_birth=student.date_of_birth,
            gender=student.gender,
            admission_date=student.admission_date,
            blood_group=student.blood_group,
            medical_notes=student.medical_notes,
            class_id=student.class_id,
            section=student.section,
            roll_number=student.roll_number,
            email=student.email,
            phone=student.phone,
            address=student.address,
            city=student.city,
            state=student.state,
            pincode=student.pincode,
            is_active=student.is_active,
            exit_date=student.exit_date,
            exit_reason=student.exit_reason,
            guardians=[
                schemas.GuardianOut.from_orm(g)
                for g in guardians
            ]
        )