from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import ChatbotConversation
from app.modules.communication.services.ai_llm_client import call_groq, client
from app.core.config import settings
from app.modules.communication.schemas import ChatbotRequest, ChatbotResponse

CHATBOT_SYSTEM_PROMPT = """You are EdVentura Assistant, a helpful and friendly AI for an Educational Operating System.
You assist users (students, teachers, parents) with queries about attendance, fees, exams, schedules, notices, and general school information.
If you don't know an answer, politely guide the user to contact their school administration.
Keep responses concise and professional.
"""

class AIChatbotService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def chat(self, request: ChatbotRequest, user_id: UUID, user_type: str) -> ChatbotResponse:
        conv = None
        if request.conversation_id:
            conv = await self.db.get(ChatbotConversation, request.conversation_id)
            if not conv or conv.tenant_id != self.tenant_id:
                conv = None

        messages_history = conv.messages if conv else []
        messages_history.append({"role": "user", "content": request.message})

        # Build full prompt with history
        # For Groq, we'll use the messages format directly with the API
        # Actually, we'll send system prompt + history
        all_messages = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}] + messages_history[-20:]  # keep last 20 messages
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL or "llama3-70b-8192",
            messages=all_messages,
            max_tokens=500,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content
        messages_history.append({"role": "assistant", "content": reply})

        if conv:
            conv.messages = messages_history
        else:
            conv = ChatbotConversation(
                tenant_id=self.tenant_id,
                user_id=user_id,
                user_type=user_type,
                messages=messages_history
            )
            self.db.add(conv)
        await self.db.commit()

        return ChatbotResponse(reply=reply, conversation_id=conv.id)