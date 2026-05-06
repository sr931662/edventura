from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import CompetitiveCohort, StudentPerformanceAnalytics, Student

class CompetitiveBenchmarkingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def upload_cohort(self, data: dict):
        cohort = CompetitiveCohort(tenant_id=self.tenant_id, **data)
        self.db.add(cohort)
        await self.db.commit()
        return cohort

    async def get_percentile(self, student_id: UUID, exam_id: UUID, cohort_id: UUID) -> dict:
        """Compute student's percentile within a given cohort based on an exam score."""
        # Fetch student's performance analytics for this exam
        perf = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.exam_id == exam_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if not perf:
            raise ValueError("No performance record found")

        cohort = await self.db.get(CompetitiveCohort, cohort_id)
        if not cohort:
            raise ValueError("Cohort not found")

        score = float(perf.percentage)
        distribution = cohort.score_distribution  # e.g., {"90": 95, "80": 80, ...} percentiles mapped
        # Determine percentile: find highest score threshold that student meets
        percentile = 0
        for threshold_str, pct in sorted(distribution.items(), key=lambda x: int(x[0]), reverse=True):
            threshold = int(threshold_str)
            if score >= threshold:
                percentile = pct
                break
        return {
            "student_score": score,
            "cohort_name": cohort.name,
            "exam_type": cohort.exam_type,
            "percentile": percentile,
            "total_participants": cohort.total_participants
        }