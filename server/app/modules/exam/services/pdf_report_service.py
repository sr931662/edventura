import os
from typing import Optional
from uuid import UUID
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exam_models import (
    StudentPerformanceAnalytics, ClassSectionAnalytics, Exam, Student,
    PDFReportLog, Subject
)
from app.models.class_ import Class
from app.core.config import settings
import weasyprint

class PDFReportService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_individual_report(self, student_id: UUID, exam_id: UUID) -> str:
        analytics = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.exam_id == exam_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if not analytics:
            raise ValueError("Analytics not found")

        student = await self.db.get(Student, student_id)
        exam = await self.db.get(Exam, exam_id)
        if not student or not exam:
            raise ValueError("Student or exam not found")
        html = f"""
        <html><body>
        <h1>Student Exam Report</h1>
        <p><strong>Student Name:</strong> {student.first_name} {student.last_name}</p>
        <p><strong>Subject:</strong> {exam.subject_id}</p>
        <p><strong>Marks Obtained:</strong> {analytics.marks_obtained}/{analytics.total_marks} ({analytics.percentage}%)</p>
        <p><strong>Class Percentile:</strong> {analytics.percentile_class}%</p>
        <h3>SWOT Analysis</h3>
        <p><strong>Strengths:</strong> {', '.join(analytics.swot_strengths)}</p>
        <p><strong>Weaknesses:</strong> {', '.join(analytics.swot_weaknesses)}</p>
        <p><strong>Opportunities:</strong> {', '.join(analytics.swot_opportunities)}</p>
        <p><strong>Threats:</strong> {', '.join(analytics.swot_threats)}</p>
        <h3>Topic-wise Performance</h3>
        <ul>
        {"".join(f"<li>{k}: {v['obtained']}/{v['total']} ({v['obtained']/v['total']*100:.1f}%)</li>" for k,v in analytics.topic_wise_breakdown.items())}
        </ul>
        <p><strong>Learning Velocity:</strong> {analytics.learning_velocity}%</p>
        <p><strong>Consistency Score:</strong> {analytics.consistency_score}</p>
        </body></html>
        """
        file_name = f"report_individual_{student_id}_{exam_id}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "reports", file_name)
        weasyprint.HTML(string=html).write_pdf(file_path)
        return file_path

    async def generate_class_report(self, class_id: UUID, exam_id: UUID) -> str:
        class_analytics = (await self.db.execute(
            select(ClassSectionAnalytics).where(
                ClassSectionAnalytics.class_id == class_id,
                ClassSectionAnalytics.exam_id == exam_id,
                ClassSectionAnalytics.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if not class_analytics:
            raise ValueError("Class analytics not found")

        class_info = await self.db.get(Class, class_id)
        if not class_info:
            raise ValueError("Class not found")
        html = f"""
        <html><body>
        <h1>Class Exam Report</h1>
        <p><strong>Class:</strong> {class_info.name} {class_info.section or ''}</p>
        <p><strong>Exam:</strong> {exam_id}</p>
        <p><strong>Average:</strong> {class_analytics.average}%</p>
        <p><strong>Median:</strong> {class_analytics.median}%</p>
        <p><strong>Highest:</strong> {class_analytics.highest}%</p>
        <p><strong>Lowest:</strong> {class_analytics.lowest}%</p>
        <p><strong>Pass Percentage:</strong> {class_analytics.pass_percentage}%</p>
        <h3>Topic-wise Average</h3>
        <ul>
        {"".join(f"<li>{k}: {v.get('average_percent',0):.1f}%</li>" for k,v in class_analytics.topic_wise_average.items())}
        </ul>
        </body></html>
        """
        file_name = f"report_class_{class_id}_{exam_id}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "reports", file_name)
        weasyprint.HTML(string=html).write_pdf(file_path)
        return file_path

    async def generate_institutional_report(self) -> str:
        # Aggregate across all classes and exams
        # For simplicity, we'll query the latest class analytics
        recent = (await self.db.execute(
            select(ClassSectionAnalytics).where(
                ClassSectionAnalytics.tenant_id == self.tenant_id
            ).order_by(ClassSectionAnalytics.created_at.desc()).limit(10)
        )).scalars().all()

        html = """<html><body><h1>Institutional Analytics Report</h1><table border='1'>
        <tr><th>Class</th><th>Subject</th><th>Average</th><th>Pass %</th></tr>"""
        for ana in recent:
            cls = await self.db.get(Class, ana.class_id)
            subj = await self.db.get(Subject, ana.subject_id) if ana.subject_id else None
            html += f"<tr><td>{cls.name if cls else ''}</td><td>{subj.name if subj else ''}</td><td>{ana.average}</td><td>{ana.pass_percentage}</td></tr>"
        html += "</table></body></html>"
        file_name = f"report_institutional_{date.today().isoformat()}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "reports", file_name)
        weasyprint.HTML(string=html).write_pdf(file_path)
        return file_path

    async def generate_report(self, report_type: str, user_id: UUID,
                              entity_id: Optional[UUID] = None, exam_id: Optional[UUID] = None) -> str:
        if report_type == "individual":
            if not entity_id or not exam_id:
                raise ValueError("student_id and exam_id required for individual report")
            path = await self.generate_individual_report(entity_id, exam_id)
        elif report_type == "class":
            if not entity_id or not exam_id:
                raise ValueError("class_id and exam_id required for class report")
            path = await self.generate_class_report(entity_id, exam_id)
        elif report_type == "institutional":
            path = await self.generate_institutional_report()
        else:
            raise ValueError("Invalid report type")

        # Log
        log = PDFReportLog(
            tenant_id=self.tenant_id,
            report_type=report_type,
            entity_id=entity_id,
            generated_by=user_id,
            file_path=path,
            generated_at=datetime.now(timezone.utc)
        )
        self.db.add(log)
        await self.db.commit()
        return path