from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import AdaptiveTestConfig, Question, StudentResponse, StudentExamRegistration

class AdaptiveTestingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_adaptive_config(self, exam_id: UUID) -> AdaptiveTestConfig:
        stmt = select(AdaptiveTestConfig).where(
            AdaptiveTestConfig.exam_id == exam_id,
            AdaptiveTestConfig.tenant_id == self.tenant_id
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_next_question_difficulty(self, reg_id: UUID, exam_id: UUID) -> str:
        """Based on previous answers, determine difficulty for next question."""
        config = await self.get_adaptive_config(exam_id)
        if not config or not config.enabled:
            return config.initial_difficulty if config else 'medium'

        # Fetch last few responses for this registration
        responses = (await self.db.execute(
            select(StudentResponse).where(
                StudentResponse.registration_id == reg_id,
                StudentResponse.tenant_id == self.tenant_id
            ).order_by(StudentResponse.created_at.desc()).limit(5)
        )).scalars().all()

        if not responses:
            return config.initial_difficulty

        # Simple rule: if last 3 answers are all correct, increase difficulty; if all wrong, decrease.
        last_three = responses[:3]
        if all(r.is_correct for r in last_three):
            return self._increase_difficulty(config.initial_difficulty)
        elif not any(r.is_correct for r in last_three):
            return self._decrease_difficulty(config.initial_difficulty)
        else:
            return config.initial_difficulty

    def _increase_difficulty(self, current: str) -> str:
        levels = ['easy', 'medium', 'hard', 'competitive']
        idx = levels.index(current) if current in levels else 1
        return levels[min(idx+1, len(levels)-1)]

    def _decrease_difficulty(self, current: str) -> str:
        levels = ['easy', 'medium', 'hard', 'competitive']
        idx = levels.index(current) if current in levels else 1
        return levels[max(idx-1, 0)]

    async def select_question_for_student(self, reg_id: UUID, exam_id: UUID, subject_id: UUID, topic_id: Optional[UUID] = None) -> Optional[Question]:
        """Pick next question based on adaptive difficulty."""
        difficulty = await self.get_next_question_difficulty(reg_id, exam_id)
        stmt = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.subject_id == subject_id,
            Question.difficulty == difficulty,
            Question.is_active == True
        )
        if topic_id:
            stmt = stmt.where(Question.topic_id == topic_id)
        result = await self.db.execute(stmt.limit(1))
        return result.scalar_one_or_none()