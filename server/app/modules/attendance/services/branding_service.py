from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.attendance_models import TenantBranding, ConsolidatedAttendance, AttendanceComputation
from uuid import UUID
from datetime import date, timedelta

class BrandingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_branding(self) -> TenantBranding | None:
        result = await self.db.execute(
            select(TenantBranding).where(TenantBranding.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def upsert_branding(self, data: dict) -> TenantBranding:
        branding = await self.get_branding()
        if branding:
            for k, v in data.items():
                setattr(branding, k, v)
        else:
            branding = TenantBranding(tenant_id=self.tenant_id, **data)
            self.db.add(branding)
        await self.db.commit()
        return branding

    async def refresh_consolidated_data(self, group_tenant_id: UUID, child_tenant_ids: list[UUID]):
        # For a chain owner, compute today's attendance across child tenants
        today = date.today()
        for ctid in child_tenant_ids:
            # aggregate class records for today from child tenant
            # Note: this query must run against the child tenant's data; for same DB, we can just filter by tenant_id.
            # Here we assume we're querying the same database but different tenant_ids.
            # We'll use a raw cross-tenant query (since multi-tenant schema isolation might be separate; if separate schemas, we'd need external APIs).
            # For a shared database, we can do:
            total = (await self.db.execute(
                select(func.count()).select_from(AttendanceComputation).where(
                    AttendanceComputation.tenant_id == ctid,
                    AttendanceComputation.date == today,
                    AttendanceComputation.student_id != None
                )
            )).scalar()
            present = (await self.db.execute(
                select(func.count()).where(AttendanceComputation.effective_present == True)
            )).scalar()
            perc = ((present or 0) / total * 100) if total else 0
            # upsert into consolidated_attendance
            existing = (await self.db.execute(
                select(ConsolidatedAttendance).where(
                    ConsolidatedAttendance.group_tenant_id == group_tenant_id,
                    ConsolidatedAttendance.child_tenant_id == ctid,
                    ConsolidatedAttendance.date == today
                )
            )).scalar_one_or_none()
            if existing:
                existing.present_count = present
                existing.total_count = total
                existing.present_percent = perc
            else:
                self.db.add(ConsolidatedAttendance(
                    group_tenant_id=group_tenant_id,
                    child_tenant_id=ctid,
                    date=today,
                    present_count=present,
                    total_count=total,
                    present_percent=perc
                ))
        await self.db.commit()