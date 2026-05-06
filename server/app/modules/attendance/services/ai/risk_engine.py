from sqlalchemy import select
from app.models.attendance_models import AttendanceComputation
from app.models.gamification_models import RiskScore
from app.models.student import Student
from datetime import date, timedelta
import numpy as np
from uuid import UUID

class RiskEngine:
    def __init__(self, db, tenant_id):
        self.db = db
        self.tenant_id = tenant_id

    async def compute_risk(self, student_id: UUID):
        # Last 30 days attendance average
        comp = await self.db.execute(
            select(AttendanceComputation).where(
                AttendanceComputation.student_id == student_id,
                AttendanceComputation.tenant_id == self.tenant_id,
                AttendanceComputation.date >= date.today() - timedelta(days=30)
            )
        )
        records = comp.scalars().all()
        if not records:
            avg_att = 100.0
        else:
            avg_att = np.mean([float(r.attendance_percent) for r in records])
        attendance_risk = max(0.0, 100.0 - avg_att)
        # Simple composite (could include academic/behavior)
        composite_risk = attendance_risk * 0.7
        # Upsert risk_scores
        existing = (await self.db.execute(
            select(RiskScore).where(
                RiskScore.student_id == student_id,
                RiskScore.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if existing:
            existing.attendance_risk = attendance_risk
            existing.composite_risk = composite_risk
            existing.factors = {"avg_attendance": avg_att}
        else:
            self.db.add(RiskScore(
                tenant_id=self.tenant_id,
                student_id=student_id,
                attendance_risk=attendance_risk,
                composite_risk=composite_risk,
                factors={"avg_attendance": avg_att}
            ))
        await self.db.commit()
        return {"attendance_risk": attendance_risk, "composite_risk": composite_risk, "avg_attendance": avg_att}