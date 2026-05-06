from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.exam_models import Question, ExamTemplate, Topic
import random

class AIQuestionGenerator:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_questions(self, template_id: UUID, exclude_used: bool = True) -> list:
        """Auto‑select questions based on blueprint in template. Returns list of (question, marks)."""
        template = await self.db.get(ExamTemplate, template_id)
        if not template or template.tenant_id != self.tenant_id:
            raise ValueError("Template not found")
        blueprint = template.blueprint  # list of dicts

        selected = []
        for section in blueprint:
            topic_id = section.get('topic_id')
            question_count = section['question_count']
            difficulty_dist = section.get('difficulty_distribution', {})
            marks_per_question = section.get('marks_per_question', 1)

            # For each difficulty, fetch matching questions
            for diff, percent in difficulty_dist.items():
                needed = max(1, int(question_count * percent / 100))
                stmt = select(Question).where(
                    Question.tenant_id == self.tenant_id,
                    Question.topic_id == topic_id,
                    Question.difficulty == diff,
                    Question.is_active == True
                ).limit(needed)
                result = await self.db.execute(stmt)
                questions = result.scalars().all()
                for q in questions:
                    selected.append((q.id, marks_per_question))
                # If not enough, fill with any difficulty later

            # Fill remaining with any active questions for the topic
            already = len([s for s in selected if s[0] in [q.id for q in await self._get_topic_questions(topic_id)]])
            remaining = question_count - already
            if remaining > 0:
                stmt = select(Question).where(
                    Question.tenant_id == self.tenant_id,
                    Question.topic_id == topic_id,
                    Question.is_active == True
                ).limit(remaining)
                result = await self.db.execute(stmt)
                extra = result.scalars().all()
                for q in extra:
                    selected.append((q.id, marks_per_question))
        return selected

    async def _get_topic_questions(self, topic_id: UUID) -> list:
        stmt = select(Question).where(Question.topic_id == topic_id, Question.tenant_id == self.tenant_id)
        res = await self.db.execute(stmt)
        return res.scalars().all()