from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import StudentPerformanceAnalytics, Topic, RevisionPlan
from app.modules.exam.exam_schemas import StudyRecommendation
from datetime import datetime, timedelta

class StudyRecommendationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_recommendations(self, student_id: UUID, subject_id: UUID) -> List[StudyRecommendation]:
        """Analyze SWOT and topic weaknesses to produce action plan."""
        analytics = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.subject_id == subject_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            ).order_by(StudentPerformanceAnalytics.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        if not analytics or not analytics.topic_wise_breakdown:
            return []

        recommendations = []
        for tid_str, data in analytics.topic_wise_breakdown.items():
            tid = UUID(tid_str)
            topic = await self.db.get(Topic, tid)
            if not topic:
                continue
            total = data.get('total', 0)
            obtained = data.get('obtained', 0)
            if total == 0:
                continue
            pct = obtained / total * 100

            actions = []
            resources = []
            if pct < 50:
                actions.append("Watch foundational videos")
                actions.append("Attempt 10 easy practice questions")
                resources.append("https://resources.edventura.com/basics/" + str(tid))
            elif pct < 70:
                actions.append("Solve mixed difficulty worksheets")
                actions.append("Review mistakes from previous tests")
                resources.append("https://resources.edventura.com/intermediate/" + str(tid))
            elif pct >= 80:
                actions.append("Attempt competitive-level challenges")
                actions.append("Peer‑teach this topic to someone else")
                resources.append("https://resources.edventura.com/advanced/" + str(tid))

            recommendations.append(StudyRecommendation(
                topic_id=tid,
                topic_name=topic.name,
                current_score=round(pct, 2),
                recommended_actions=actions,
                resources=resources
            ))
        return recommendations

    async def generate_revision_plan(self, student_id: UUID, subject_id: UUID, days: int = 7) -> RevisionPlan:
        """Create a daily schedule covering weak topics, evenly distributed."""
        analytics = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.subject_id == subject_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            ).order_by(StudentPerformanceAnalytics.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        if not analytics or not analytics.topic_wise_breakdown:
            raise ValueError("No analytics available")

        # Sort topics by weakness
        weak_topics = []
        for tid_str, data in analytics.topic_wise_breakdown.items():
            total = data['total']
            obtained = data['obtained']
            if total > 0 and obtained / total < 0.8:
                weak_topics.append((UUID(tid_str), obtained/total))
        weak_topics.sort(key=lambda x: x[1])

        if not weak_topics:
            # If no weaknesses, just pick random topics
            weak_topics = [(UUID(tid_str), 0.5) for tid_str in analytics.topic_wise_breakdown.keys()][:3]

        plan = {}
        for day_offset in range(days):
            day = (datetime.utcnow() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
            # Assign 2 topics per day
            todays_topics = [weak_topics[i % len(weak_topics)][0] for i in range(day_offset*2, day_offset*2+2)]
            plan[day] = {
                "topics": [str(t) for t in todays_topics],
                "actions": ["Review notes", "Attempt 10 questions", "Take mini‑quiz"]
            }

        revision = RevisionPlan(
            tenant_id=self.tenant_id,
            student_id=student_id,
            subject_id=subject_id,
            plan_data=plan,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=days)
        )
        self.db.add(revision)
        await self.db.commit()
        return revision

    async def get_revision_plan(self, student_id: UUID, subject_id: UUID) -> Optional[RevisionPlan]:
        stmt = select(RevisionPlan).where(
            RevisionPlan.student_id == student_id,
            RevisionPlan.subject_id == subject_id,
            RevisionPlan.tenant_id == self.tenant_id,
            RevisionPlan.expires_at > datetime.utcnow()
        ).order_by(RevisionPlan.generated_at.desc()).limit(1)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()