from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import ExternalWebhook
import httpx
import json

class WebhookService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def register_webhook(self, data: dict) -> ExternalWebhook:
        webhook = ExternalWebhook(tenant_id=self.tenant_id, **data)
        self.db.add(webhook)
        await self.db.commit()
        return webhook

    async def dispatch_event(self, event_type: str, event_data: dict):
        """Send event to all active webhooks that subscribe to it."""
        webhooks = (await self.db.execute(
            select(ExternalWebhook).where(
                ExternalWebhook.tenant_id == self.tenant_id,
                ExternalWebhook.is_active == True,
                ExternalWebhook.event_types.contains([event_type])
            )
        )).scalars().all()
        async with httpx.AsyncClient() as client:
            for wh in webhooks:
                try:
                    await client.post(wh.url, json=event_data, headers={
                        "X-Webhook-Secret": wh.secret_key,
                        "Content-Type": "application/json"
                    }, timeout=10)
                except Exception:
                    pass