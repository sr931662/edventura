from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.communication_models import Survey, SurveyResponse
from app.modules.communication.schemas import SurveyCreate, SurveyResponseCreate, NotificationCreate
from app.modules.communication.services.notification_service import NotificationService
from datetime import datetime

class SurveyService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def create_survey(self, data: SurveyCreate, created_by: UUID) -> Survey:
        survey = Survey(
            tenant_id=self.tenant_id,
            title=data.title,
            description=data.description,
            survey_type=data.survey_type,
            questions=[q.dict() for q in data.questions],
            target_audience=data.target_audience or [],
            is_anonymous=data.is_anonymous,
            open_at=data.open_at or datetime.utcnow(),
            close_at=data.close_at,
            created_by=created_by,
            status='draft'
        )
        self.db.add(survey)
        await self.db.commit()
        return survey

    async def publish_survey(self, survey_id: UUID) -> Optional[Survey]:
        survey = await self.db.get(Survey, survey_id)
        if not survey or survey.tenant_id != self.tenant_id:
            return None
        survey.status = 'published'
        # Notify target audience
        for entry in survey.target_audience or []:
            user_id = entry.get('user_id')
            user_type = entry.get('user_type', 'student')
            if user_id:
                await self.notif_svc.send_notification(NotificationCreate(
                    recipient_id=UUID(user_id),
                    recipient_type=user_type,
                    title=f"New {survey.survey_type}: {survey.title}",
                    body=survey.description or "Please participate",
                    category="survey",
                    channel="in_app",
                    meta_data={"survey_id": str(survey.id)}
                ))
        await self.db.commit()
        return survey

    async def submit_response(self, survey_id: UUID, respondent_id: UUID, respondent_type: str, answers: List[dict]) -> SurveyResponse:
        resp = SurveyResponse(
            tenant_id=self.tenant_id,
            survey_id=survey_id,
            respondent_id=respondent_id,
            respondent_type=respondent_type,
            answers=answers
        )
        self.db.add(resp)
        await self.db.commit()
        return resp

    async def get_survey_results(self, survey_id: UUID) -> dict:
        survey = await self.db.get(Survey, survey_id)
        if not survey:
            return {}
        responses = (await self.db.execute(
            select(SurveyResponse).where(SurveyResponse.survey_id == survey_id, SurveyResponse.tenant_id == self.tenant_id)
        )).scalars().all()
        total = len(responses)
        aggregation = {}
        for i, q in enumerate(survey.questions):
            key = q.get('question_text', f"Q{i+1}")
            if q.get('question_type') in ('multiple_choice', 'single_choice', 'yes_no'):
                counts = {}
                for r in responses:
                    ans = r.answers[i].get('answer') if i < len(r.answers) else None
                    if ans:
                        counts[ans] = counts.get(ans, 0) + 1
                aggregation[key] = {"type": "choices", "data": counts}
            else:
                aggregation[key] = {"type": "text", "responses": [r.answers[i].get('answer') for r in responses if i < len(r.answers)]}
        return {"total_responses": total, "aggregation": aggregation}