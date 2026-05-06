"""
POST  /api/v1/assistant/chat   — authenticated, streams Daisy's reply

Registration (add to app/main.py):
    from app.modules.assistant.router import router as assistant_router
    app.include_router(assistant_router, prefix="/api/v1/assistant", tags=["assistant"])
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.role import Role
from app.models.user_role import user_roles
from app.models.permission import Permission
from app.models.role_permission import role_permissions

from sqlalchemy import select
from app.modules.assistant.schemas import ChatRequest, ChatResponse, DaisyContext
from app.modules.assistant.service import daisy_service

router = APIRouter()


async def _build_context(user: User, db: AsyncSession) -> DaisyContext:
    """
    Fetch the user's roles and permissions from DB so Daisy has full context.
    Falls back to empty lists if relationships aren't loaded.
    """
    # Fetch roles
    role_stmt = (
        select(Role.name)
        .join(user_roles, Role.id == user_roles.c.role_id)
        .where(user_roles.c.user_id == user.id)
    )
    role_rows = (await db.execute(role_stmt)).scalars().all()
    roles = list(role_rows)

    # Fetch permissions via roles
    perm_stmt = (
        select(Permission.codename)
        .join(role_permissions, Permission.id == role_permissions.c.permission_id)
        .join(user_roles, role_permissions.c.role_id == user_roles.c.role_id)
        .where(user_roles.c.user_id == user.id)
        .distinct()
    )
    perm_rows = (await db.execute(perm_stmt)).scalars().all()
    permissions = list(perm_rows)

    return DaisyContext(
        user_id=str(user.id),
        full_name=user.full_name or "",
        roles=roles,
        permissions=permissions,
        is_super_admin=user.is_super_admin,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )


@router.post("/chat", response_model=ChatResponse, summary="Chat with Daisy")
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Send a message to Daisy and receive an AI-powered, role-aware reply.

    - **message**: The user's natural-language query (English / Hindi / Hinglish)
    - **history**: Previous conversation turns (last 20 max; client manages this)

    The endpoint:
    1. Builds a DaisyContext from the authenticated user's DB roles & permissions
    2. Constructs a role-aware system prompt
    3. Calls Groq Llama 3 70B for NLP-powered response generation
    4. Returns the reply and a classified intent label
    """
    ctx = await _build_context(current_user, db)
    reply, intent = await daisy_service.chat(ctx, body.message, body.history)

    return ChatResponse(reply=reply, intent=intent)