from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.models.student import Student, Guardian
from typing import Any, Optional, List
from uuid import UUID

class StudentRepository:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create(self, data: dict, guardians_data: Optional[List[dict]] = None) -> Student:
        data["tenant_id"] = self.tenant_id
        student = Student(**data)
        self.db.add(student)
        if guardians_data:
            for gdata in guardians_data:
                gdata["tenant_id"] = self.tenant_id
                guardian = Guardian(**gdata)
                student.guardians.append(guardian)
        await self.db.commit()
        await self.db.refresh(student)
        return student

    async def get_by_id(self, student_id: UUID) -> Optional[Student]:
        stmt = select(Student).options(selectinload(Student.guardians)).where(
            Student.id == student_id,
            Student.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_students(
        self,
        class_id: Optional[UUID] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Student]:
        stmt = select(Student).options(selectinload(Student.guardians)).where(
            Student.tenant_id == self.tenant_id
        )
        if class_id is not None:
            stmt = stmt.where(Student.class_id == class_id)
        if is_active is not None:
            stmt = stmt.where(Student.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, student_id: UUID, data: dict) -> Optional[Student]:
        data.pop("tenant_id", None)
        # Ensure tenant scoping
        stmt = (
            update(Student)
            .where(Student.id == student_id, Student.tenant_id == self.tenant_id)
            .values(**data)
            .returning(Student)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def delete(self, student_id: UUID) -> bool:
        stmt = delete(Student).where(
            Student.id == student_id,
            Student.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def exit_student(self, student_id: UUID, reason: str, exit_date):
        return await self.update(student_id, {
            "is_active": False,
            "exit_date": exit_date,
            "exit_reason": reason
        })

    async def bulk_promote(self, from_class_id: UUID, to_class_id: UUID, section: Optional[str] = None):
        values: dict[str, Any] = {"class_id": to_class_id}
        if section:
            values["section"] = section
        stmt = (
            update(Student)
            .where(
                Student.class_id == from_class_id,
                Student.tenant_id == self.tenant_id,
                Student.is_active == True
            )
            .values(**values)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount