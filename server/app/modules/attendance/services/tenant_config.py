from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.attendance_models import AttendancePolicy
from typing import Any, Dict, Optional
from uuid import UUID

class TenantConfigService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_policy(self) -> Optional[AttendancePolicy]:
        stmt = select(AttendancePolicy).where(
            AttendancePolicy.tenant_id == self.tenant_id,
            AttendancePolicy.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_config(self) -> Dict[str, Any]:
        policy = await self.get_policy()
        if policy:
            return policy.config
        # create default
        default = {
            "school_type": "day_school",
            "late_grace_minutes": 15,
            "half_day_threshold_hours": 3,
            "min_attendance_percent": 75,
            "enabled_marking_methods": ["manual", "biometric", "qr"]
        }
        await self.update_config(default)
        return default

    async def get_rule(self, rule_name: str) -> Any:
        config = await self.get_config()
        return config.get(rule_name)

    async def get_marking_methods(self) -> list:
        config = await self.get_config()
        return config.get("enabled_marking_methods", ["manual"])

    async def update_config(self, new_config: Dict) -> AttendancePolicy:
        policy = await self.get_policy()
        if policy:
            policy.config = new_config
        else:
            policy = AttendancePolicy(tenant_id=self.tenant_id, name="Default", config=new_config)
            self.db.add(policy)
        await self.db.commit()
        return policy