import os
from datetime import date, timedelta
from pydoc import html
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.attendance_models import AttendanceComputation, ComplianceDocument
from app.models.student import Student
from app.modules.attendance.event_publisher import publish_event
from app.core.config import settings


class ComplianceService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_warning_letter(self, student_id: UUID):
        student = await self.db.get(Student, student_id)
        if not student:
            return None
        # check attendance
        avg_res = await self.db.execute(
            select(func.avg(AttendanceComputation.attendance_percent))
            .where(AttendanceComputation.student_id == student_id, AttendanceComputation.tenant_id == self.tenant_id)
        )
        avg = avg_res.scalar() or 100
        min_req = 75.0
        if avg >= min_req:
            return None
        # Generate PDF using WeasyPrint
        html = f"<h1>Warning Letter</h1><p>Dear Parent, your child {student.first_name} has attendance below {min_req}% ...</p>"
        file_name = f"warning_{student_id}_{date.today().isoformat()}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "compliance", file_name)
                
        import weasyprint
        weasyprint.HTML(string=html).write_pdf(file_path)

        doc = ComplianceDocument(
            tenant_id=self.tenant_id,
            student_id=student_id,
            doc_type='warning_letter',
            file_path=file_path,
            status='generated'
        )
        self.db.add(doc)
        await self.db.commit()
        return doc

    async def check_and_enforce(self):
        # nightly job: for all students below threshold, generate warning if not already generated in 30 days
        students = await self.db.execute(
            select(Student).where(Student.tenant_id == self.tenant_id, Student.is_active == True)
        )
        for s in students.scalars():
            avg_res = await self.db.execute(
                select(func.avg(AttendanceComputation.attendance_percent))
                .where(AttendanceComputation.student_id == s.id, AttendanceComputation.tenant_id == self.tenant_id)
            )
            avg = avg_res.scalar() or 100
            if avg < 75:
                # check if warning sent recently
                recent = await self.db.execute(
                    select(ComplianceDocument).where(
                        ComplianceDocument.student_id == s.id,
                        ComplianceDocument.doc_type == 'warning_letter',
                        ComplianceDocument.generated_at >= date.today() - timedelta(days=30)
                    )
                )
                if not recent.scalar_one_or_none():
                    doc = await self.generate_warning_letter(s.id)
                    if doc:
                        # trigger notification
                        await publish_event("attendance_events", {
                            "type": "WarningLetterGenerated",
                            "student_id": str(s.id),
                            "document_id": str(doc.id)
                        })

    async def generate_board_report(self, board_type: str, academic_year: str):
        # simplified: query aggregated data and produce PDF
        # real implementation would fetch specific categories
        html = f"<h1>{board_type} Attendance Register {academic_year}</h1>"
        # ...
        return {"message": "Board report generated"}