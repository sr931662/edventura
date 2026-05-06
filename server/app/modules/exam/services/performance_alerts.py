from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import StudentPerformanceAnalytics, Student
from app.modules.attendance.event_publisher import publish_event

class PerformanceAlertService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def check_and_alert(self, student_id: UUID, subject_id: UUID):
        """If latest analytics show drop >20% vs previous, publish alert."""
        analytics = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.subject_id == subject_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            ).order_by(StudentPerformanceAnalytics.created_at.desc()).limit(2)
        )).scalars().all()
        if len(analytics) < 2:
            return
        latest = analytics[0]
        previous = analytics[1]
        if latest.percentage and previous.percentage:
            drop = float(previous.percentage) - float(latest.percentage)
            if drop > 20:
                await publish_event("exam_events", {
                    "type": "PerformanceDropAlert",
                    "tenant_id": str(self.tenant_id),
                    "student_id": str(student_id),
                    "subject_id": str(subject_id),
                    "drop_percent": drop
                })
                
    async def check_toppers(self, exam_id: UUID):
        """Fetch top 3 students and publish topper alert."""
        toppers = (await self.db.execute(
            select(StudentPerformanceAnalytics.student_id, StudentPerformanceAnalytics.percentage, Student.first_name, Student.last_name)
            .join(Student, StudentPerformanceAnalytics.student_id == Student.id)
            .where(StudentPerformanceAnalytics.exam_id == exam_id, StudentPerformanceAnalytics.tenant_id == self.tenant_id)
            .order_by(StudentPerformanceAnalytics.percentage.desc()).limit(3)
        )).all()
        for t in toppers:
            await publish_event("exam_events", {
                "type": "TopperAlert",
                "tenant_id": str(self.tenant_id),
                "student_id": str(t.student_id),
                "student_name": f"{t.first_name} {t.last_name}",
                "percentage": float(t.percentage)
            })

    async def check_dropout_risk(self):
        """Identify students with consecutive drops in two exams."""
        # Get all analytics ordered by student, subject, date
        analytics = (await self.db.execute(
            select(StudentPerformanceAnalytics)
            .where(StudentPerformanceAnalytics.tenant_id == self.tenant_id)
            .order_by(StudentPerformanceAnalytics.student_id, StudentPerformanceAnalytics.created_at)
        )).scalars().all()
        # Group by student
        from collections import defaultdict
        student_groups = defaultdict(list)
        for a in analytics:
            student_groups[a.student_id].append(a)
        risky = []
        for sid, records in student_groups.items():
            if len(records) >= 3:
                last_three = records[-3:]
                percentages = [float(r.percentage) for r in last_three if r.percentage]
                if len(percentages) >= 3 and percentages[0] > percentages[1] > percentages[2]:
                    # three consecutive drops
                    risky.append({
                        "student_id": sid,
                        "risk_level": "high",
                        "consecutive_drops": 3
                    })
                    await publish_event("exam_events", {
                        "type": "DropoutRisk",
                        "tenant_id": str(self.tenant_id),
                        "student_id": str(sid),
                        "risk_level": "high"
                    })
        return risky