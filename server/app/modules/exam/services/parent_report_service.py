from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import ParentExamReport, StudentPerformanceAnalytics, Exam, Student
from app.models.student import Student as StudentModel
from datetime import datetime

class ParentReportService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_parent_report(self, student_id: UUID, exam_id: UUID) -> ParentExamReport:
        student = await self.db.get(StudentModel, student_id)
        exam = await self.db.get(Exam, exam_id)
        perf = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.exam_id == exam_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()

        if not student or not exam or not perf:
            raise ValueError("Data not found")

        html = f"""
        <html><body>
        <h2>Student Performance Report</h2>
        <p><strong>Student:</strong> {student.first_name} {student.last_name}</p>
        <p><strong>Exam:</strong> {exam.title}</p>
        <p><strong>Marks:</strong> {perf.marks_obtained}/{perf.total_marks} ({perf.percentage}%)</p>
        <p><strong>Status:</strong> {'Passed' if float(perf.percentage) >= exam.passing_marks else 'Needs Improvement'}</p>
        <h3>Strengths</h3>
        <ul>{"".join(f"<li>{s}</li>" for s in (perf.swot_strengths or []))}</ul>
        <h3>Areas to Improve</h3>
        <ul>{"".join(f"<li>{s}</li>" for s in (perf.swot_weaknesses or []))}</ul>
        <p><em>Generated on {datetime.utcnow().strftime('%Y-%m-%d')}</em></p>
        </body></html>
        """
        report = ParentExamReport(
            tenant_id=self.tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            summary_html=html,
            generated_at=datetime.utcnow()
        )
        self.db.add(report)
        await self.db.commit()
        return report

    async def get_report(self, student_id: UUID, exam_id: UUID) -> Optional[ParentExamReport]:
        stmt = select(ParentExamReport).where(
            ParentExamReport.student_id == student_id,
            ParentExamReport.exam_id == exam_id,
            ParentExamReport.tenant_id == self.tenant_id
        ).order_by(ParentExamReport.generated_at.desc()).limit(1)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()