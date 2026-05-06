from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exam_models import StudentPerformanceAnalytics, Student
from app.models.student import Student as StudentModel
import weasyprint
import os
from datetime import date
from app.core.config import settings

class CertificateService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_certificate(self, student_id: UUID, exam_id: UUID) -> str:
        student = await self.db.get(StudentModel, student_id)
        analytics = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.exam_id == exam_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()

        if not student or not analytics:
            raise ValueError("Student or analytics not found")

        html = f"""
        <html><body style="text-align:center; font-family:serif;">
        <h1>Certificate of Achievement</h1>
        <p>This is to certify that <strong>{student.first_name} {student.last_name}</strong></p>
        <p>has successfully completed the examination with a score of <strong>{analytics.marks_obtained}/{analytics.total_marks}</strong> ({analytics.percentage}%)</p>
        <p>Date: {date.today().isoformat()}</p>
        </body></html>
        """
        file_name = f"certificate_{student_id}_{exam_id}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "certificates", file_name)
        weasyprint.HTML(string=html).write_pdf(file_path)
        return file_path

    async def generate_transcript(self, student_id: UUID) -> str:
        # Aggregate all exams for a transcript
        analytics_list = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            )
        )).scalars().all()
        student = await self.db.get(StudentModel, student_id)
        if not student:
            raise ValueError("Student not found")
        html = f"""
        <html><body>
        <h1>Academic Transcript</h1>
        <p><strong>Student:</strong> {student.first_name} {student.last_name}</p>
        <table border='1'>
        <tr><th>Subject</th><th>Marks</th><th>Percentage</th></tr>
        """
        for a in analytics_list:
            html += f"<tr><td>{a.subject_id}</td><td>{a.marks_obtained}/{a.total_marks}</td><td>{a.percentage}%</td></tr>"
        html += "</table></body></html>"
        file_name = f"transcript_{student_id}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "transcripts", file_name)
        weasyprint.HTML(string=html).write_pdf(file_path)
        return file_path