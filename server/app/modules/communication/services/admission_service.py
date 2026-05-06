from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import AdmissionCampaign, AdmissionEnquiry
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import NotificationCreate

class AdmissionService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    async def create_campaign(self, data: dict, created_by: UUID) -> AdmissionCampaign:
        campaign = AdmissionCampaign(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(campaign)
        await self.db.commit()
        return campaign

    async def list_campaigns(self) -> List[AdmissionCampaign]:
        stmt = select(AdmissionCampaign).where(AdmissionCampaign.tenant_id == self.tenant_id)
        result = await self.db.execute(stmt.order_by(AdmissionCampaign.start_date.desc()))
        return result.scalars().all()

    async def submit_enquiry(self, data: dict) -> AdmissionEnquiry:
        enquiry = AdmissionEnquiry(tenant_id=self.tenant_id, **data)
        self.db.add(enquiry)
        await self.db.commit()
        # Notify admission counselor
        await self.notif_svc.send_notification(NotificationCreate(
            recipient_id=UUID("00000000-0000-0000-0000-000000000001"),  # counselor role user
            recipient_type="staff",
            title=f"New Enquiry: {data.get('prospect_name')}",
            body=f"Grade: {data.get('student_grade', 'N/A')}",
            category="admission",
            channel="in_app"
        ))
        return enquiry

    async def list_enquiries(self, campaign_id: UUID = None) -> List[AdmissionEnquiry]:
        stmt = select(AdmissionEnquiry).where(AdmissionEnquiry.tenant_id == self.tenant_id)
        if campaign_id:
            stmt = stmt.where(AdmissionEnquiry.campaign_id == campaign_id)
        result = await self.db.execute(stmt.order_by(AdmissionEnquiry.created_at.desc()))
        return result.scalars().all()