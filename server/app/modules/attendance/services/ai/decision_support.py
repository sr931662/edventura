from sqlalchemy import select


class DecisionSupport:
    async def get_recommendations(self, student_id, db, tenant_id):
        from app.models.gamification_models import RiskScore
        risk = await db.execute(
            select(RiskScore).where(RiskScore.student_id == student_id, RiskScore.tenant_id == tenant_id)
        )
        risk = risk.scalar_one_or_none()
        if risk and risk.composite_risk > 70:
            return ["Schedule parent meeting", "Arrange remedial classes"]
        return []