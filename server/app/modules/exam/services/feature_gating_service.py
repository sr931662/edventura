from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import FeatureGate

class FeatureGatingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def is_feature_enabled(self, feature_name: str) -> bool:
        stmt = select(FeatureGate).where(
            FeatureGate.tenant_id == self.tenant_id,
            FeatureGate.feature_name == feature_name
        )
        res = await self.db.execute(stmt)
        gate = res.scalar_one_or_none()
        return gate.enabled if gate else False

    async def set_feature(self, feature_name: str, enabled: bool) -> FeatureGate:
        stmt = select(FeatureGate).where(
            FeatureGate.tenant_id == self.tenant_id,
            FeatureGate.feature_name == feature_name
        )
        gate = (await self.db.execute(stmt)).scalar_one_or_none()
        if gate:
            gate.enabled = enabled
        else:
            gate = FeatureGate(tenant_id=self.tenant_id, feature_name=feature_name, enabled=enabled)
            self.db.add(gate)
        await self.db.commit()
        return gate

    async def get_all_features(self) -> list:
        stmt = select(FeatureGate).where(FeatureGate.tenant_id == self.tenant_id)
        res = await self.db.execute(stmt)
        return res.scalars().all()