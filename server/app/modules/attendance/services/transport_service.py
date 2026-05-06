from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.event_publisher import publish_event

class TransportService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = AttendanceRepository(db, tenant_id)

    async def record_scan(self, data: dict):
        await self.repo.record_transport_scan(data)
        await publish_event("attendance_events", {
            "type": "TransportBoardingEvent",
            "tenant_id": str(self.repo.tenant_id),
            "student_id": str(data["student_id"]),
            "route_id": str(data["route_id"]),
            "type": data["type"],
            "timestamp": data["timestamp"].isoformat()
        })