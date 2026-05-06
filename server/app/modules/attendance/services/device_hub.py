from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.attendance_models import Device, QRCheckinLog, BLENFCLog, BiometricTemplate, AttendanceRecord
from app.modules.attendance.services.marking import AttendanceMarkingService
from app.modules.attendance.event_publisher import publish_event
from datetime import datetime
import json

class DeviceHubService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.marking_service = AttendanceMarkingService(db, tenant_id)

    async def register_device(self, data: dict) -> Device:
        device = Device(tenant_id=self.tenant_id, **data)
        self.db.add(device)
        await self.db.commit()
        return device

    async def handle_device_event(self, event_type: str, payload: dict):
        if event_type == "qr_scan":
            return await self._handle_qr(payload)
        elif event_type == "ble_nfc":
            return await self._handle_ble(payload)
        # other event types can be added
        else:
            raise ValueError(f"Unknown event type: {event_type}")

    async def _handle_qr(self, payload: dict):
        student_id = payload.get("student_id")
        employee_id = payload.get("employee_id")
        scan_time = payload.get("scan_time")
        device_id = payload.get("device_id")
        # Insert log
        log = QRCheckinLog(
            tenant_id=self.tenant_id,
            student_id=student_id,
            employee_id=employee_id,
            scan_time=scan_time,
            device_id=device_id
        )
        self.db.add(log)

        # Mark attendance based on who scanned
        if student_id:
            record = AttendanceRecord(
                tenant_id=self.tenant_id,
                student_id=student_id,
                attendance_type="student_class",
                date=scan_time.date(),
                in_time=scan_time.time(),
                status="present",
                device_id=str(device_id),
                verification_method="qr",
                marked_by=student_id,   # self
                marked_source="device"
            )
            self.db.add(record)
            await publish_event("attendance_events", {
                "type": "QRScanMarkedEvent",
                "tenant_id": str(self.tenant_id),
                "student_id": str(student_id),
                "timestamp": scan_time.isoformat()
            })
        # Similarly for employee
        await self.db.commit()
        return {"status": "ok"}

    async def _handle_ble(self, payload: dict):
        # For BLE/NFC, we check known student/employee and mark if within schedule
        user_id = payload.get("user_id")
        user_type = payload.get("user_type")
        device_id = payload.get("device_id")
        event_time = payload.get("event_time")
        log = BLENFCLog(
            tenant_id=self.tenant_id,
            student_id=user_id if user_type=="student" else None,
            employee_id=user_id if user_type=="employee" else None,
            event_time=event_time,
            device_id=device_id
        )
        self.db.add(log)
        # Mark attendance similar to QR but maybe check timetable proximity
        # For now simple present mark
        if user_type == "student":
            rec = AttendanceRecord(
                tenant_id=self.tenant_id,
                student_id=user_id,
                attendance_type="student_class",
                date=event_time.date(),
                in_time=event_time.time(),
                status="present",
                device_id=str(device_id),
                verification_method="ble_nfc",
                marked_by=user_id,
                marked_source="device"
            )
            self.db.add(rec)
            await publish_event("attendance_events", {
                "type": "BiometricMarkedEvent",   # reuse
                "tenant_id": str(self.tenant_id),
                "student_id": str(user_id)
            })
        await self.db.commit()
        return {"status": "ok"}

    # Biometric capture – handle template registration and future matching
    async def register_template(self, user_id, user_type, template_data, device_type):
        template = BiometricTemplate(
            tenant_id=self.tenant_id,
            user_id=user_id,
            user_type=user_type,
            template_data=template_data,
            device_type=device_type
        )
        self.db.add(template)
        await self.db.commit()
        return template

    async def match_biometric(self, user_id, template_data):
        # In real world, compare with stored template; here we just simulate
        # but for marking, we assume the device has already matched and just sends event
        # So this method is placeholder for future
        pass