from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.communication_models import AIDraftLog
from app.modules.communication.services.ai_llm_client import call_groq
from app.modules.communication.schemas import AIDraftRequest, AIDraftOut

DRAFT_SYSTEM_PROMPT = """You are an expert educational communication assistant for EdVentura, an Educational Operating System.
You craft professional, clear, and effective messages for schools.
Always output in JSON format: {"title": "...", "body": "..."}
Keep messages appropriate for the audience (parents, students, staff).
Use the specified tone.
"""

class AIDraftingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def draft_message(self, request: AIDraftRequest, created_by: UUID) -> AIDraftOut:
        # Build prompt
        key_points = "\n".join(f"- {p}" for p in request.key_points)
        user_prompt = f"""Context: {request.context_type}
Audience: {request.audience}
Tone: {request.tone}
Key points to include:
{key_points}

Craft a message (title and body) for this communication."""
        result = await call_groq(user_prompt, DRAFT_SYSTEM_PROMPT)
        response_text = result["text"]
        # Parse JSON from response
        import json
        try:
            # Sometimes response contains extra text; find JSON object
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            parsed = json.loads(response_text[start:end])
            title = parsed.get("title", "Untitled")
            body = parsed.get("body", response_text)
        except:
            title = "Draft Message"
            body = response_text

        # Log
        self.db.add(AIDraftLog(
            tenant_id=self.tenant_id,
            prompt=user_prompt,
            response=response_text,
            model=result["model"],
            tokens_used=result.get("tokens"),
            created_by=created_by
        ))
        await self.db.commit()

        return AIDraftOut(title=title, body=body, model=result["model"], tokens_used=result.get("tokens"))