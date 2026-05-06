from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatHistoryItem(BaseModel):
    """A single turn in the conversation history."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Incoming chat request from the desktop client."""
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[ChatHistoryItem] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    """Daisy's reply sent back to the client."""
    reply: str
    intent: Optional[str] = None       # navigation | permission_check | how_to | general
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DaisyContext(BaseModel):
    """Internal context built from the authenticated user — passed to the NLP service."""
    user_id: str
    full_name: str
    roles: List[str]
    permissions: List[str]
    is_super_admin: bool
    tenant_id: Optional[str] = None