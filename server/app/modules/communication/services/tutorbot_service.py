from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import TutorBotSession
from app.modules.communication.services.ai_llm_client import call_groq, client
from app.core.config import settings

TUTORBOT_SYSTEM_PROMPT = """You are TutorBot, an AI tutor integrated into EdVentura (Educational Operating System).
Your purpose is to help students understand academic concepts by providing clear, accurate, and age-appropriate explanations.
You respond in a friendly, encouraging tone and never provide harmful or inappropriate content.

Guidelines:
- Explain concepts step by step, using simple language.
- Provide examples where appropriate.
- If a student is struggling, offer hints rather than direct answers.
- When relevant, suggest further learning resources or practice problems.
- If asked about topics outside your knowledge, politely guide the student to ask their teacher.
- Keep responses concise, typically under 300 words unless the student asks for more detail.

Current context:
- Subject: {subject}
- Topic: {topic}
"""

class TutorBotService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def ask(self, student_id: UUID, message: str, subject: str = None, topic: str = None,
                  session_id: UUID = None) -> dict:
        # Get or create session
        session = None
        if session_id:
            session = await self.db.get(TutorBotSession, session_id)
            if not session or session.tenant_id != self.tenant_id:
                session = None

        if not session:
            session = TutorBotSession(
                tenant_id=self.tenant_id,
                student_id=student_id,
                subject=subject,
                topic=topic,
                messages=[]
            )
            self.db.add(session)
            await self.db.flush()

        # Build messages for LLM
        system_prompt = TUTORBOT_SYSTEM_PROMPT.format(
            subject=session.subject or "General",
            topic=session.topic or "General"
        )
        messages = [{"role": "system", "content": system_prompt}]
        # Include last 20 messages from history
        history = session.messages or []
        for msg in history[-20:]:
            messages.append(msg)
        # Add new user message
        messages.append({"role": "user", "content": message})

        # Call Groq
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL or "llama3-70b-8192",
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content

        # Update session
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        session.messages = history
        await self.db.commit()

        return {
            "reply": reply,
            "session_id": session.id,
            "subject": session.subject,
            "topic": session.topic
        }

    async def get_session_history(self, student_id: UUID, session_id: UUID = None) -> list:
        if session_id:
            session = await self.db.get(TutorBotSession, session_id)
            if session and session.tenant_id == self.tenant_id and session.student_id == student_id:
                return [session]
            return []
        # Return all sessions for student
        stmt = select(TutorBotSession).where(
            TutorBotSession.student_id == student_id,
            TutorBotSession.tenant_id == self.tenant_id
        ).order_by(TutorBotSession.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def close_session(self, session_id: UUID, student_id: UUID) -> bool:
        session = await self.db.get(TutorBotSession, session_id)
        if not session or session.tenant_id != self.tenant_id or session.student_id != student_id:
            return False
        session.status = 'closed'
        await self.db.commit()
        return True