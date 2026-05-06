from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.event_publisher import publish_event

class LeaveService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = AttendanceRepository(db, tenant_id)

    async def apply_leave(self, data: dict):
        return await self.repo.apply_leave(data)

    async def approve_leave(self, leave_id: UUID, approved_by: UUID, status: str):
        leave = await self.repo.approve_leave(leave_id, approved_by, status)
        if leave and status == "approved":
            await publish_event("attendance_events", {
                "type": "LeaveApprovedEvent",
                "tenant_id": str(self.repo.tenant_id),
                "employee_id": str(leave.employee_id),
                "from_date": leave.from_date.isoformat(),
                "to_date": leave.to_date.isoformat()
            })
        return leave

    async def get_employee_leaves(self, employee_id: UUID):
        return await self.repo.get_employee_leaves(employee_id)