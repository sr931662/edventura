from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from uuid import UUID
from datetime import date, timedelta
from app.models.attendance_models import AttendanceComputation, AttendanceRecoverySession
from app.models.student import Student
from app.models.class_ import Class
from app.models.attendance_models import TeacherClassAssignment

class RecoveryService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_proposals(self, min_percent: float = 75.0):
        # Find students below threshold based on latest computations
        thirty_days_ago = date.today() - timedelta(days=30)
        subq = (
            select(
                AttendanceComputation.student_id,
                func.avg(AttendanceComputation.attendance_percent).label('avg_percent')
            )
            .where(
                AttendanceComputation.tenant_id == self.tenant_id,
                AttendanceComputation.date >= thirty_days_ago,
                AttendanceComputation.student_id != None
            )
            .group_by(AttendanceComputation.student_id)
            .having(func.avg(AttendanceComputation.attendance_percent) < min_percent)
            .subquery()
        )
        students = await self.db.execute(
            select(Student).join(subq, Student.id == subq.c.student_id)
        )
        deficient = students.scalars().all()

        proposals = []
        for student in deficient:
            # Find their class and subjects
            cls = await self.db.get(Class, student.class_id)
            # For simplicity, pick a subject (e.g., first subject in class)
            # But subject assignment is not fully implemented; we'll skip subject for now.
            # Suggest a recovery session on the nearest weekend with a random teacher.
            proposed_date = date.today() + timedelta(days=(5 - date.today().weekday()) % 7)  # next Saturday
            # Find a teacher assigned to that class
            teacher_assign = await self.db.execute(
                select(TeacherClassAssignment).where(
                    TeacherClassAssignment.class_id == student.class_id,
                    TeacherClassAssignment.is_deleted == False
                ).limit(1)
            )
            teacher_id = teacher_assign.scalar_one_or_none()
            if not teacher_id:
                continue
            session = AttendanceRecoverySession(
                tenant_id=self.tenant_id,
                subject_id=None,  # could be a specific subject
                teacher_id=teacher_id.teacher_id,
                scheduled_date=proposed_date,
                duration_minutes=60,
                max_capacity=10,
                reason=f"Recovery for student {student.first_name} {student.last_name}",
                status="proposed"
            )
            self.db.add(session)
            proposals.append(session)
        await self.db.commit()
        return proposals

    async def confirm_session(self, session_id: UUID):
        session = await self.db.get(AttendanceRecoverySession, session_id)
        if not session or session.tenant_id != self.tenant_id:
            raise ValueError("Session not found")
        session.status = "confirmed"
        await self.db.commit()