import asyncio
import json
from app.core.redis import redis_client
from app.core.database import async_session_factory
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.services.template_service import TemplateService  # not needed directly, but available
from app.modules.communication.schemas import NotificationCreate
from uuid import UUID

EVENT_HANDLERS = {}

def register_handler(event_type: str):
    def decorator(func):
        EVENT_HANDLERS[event_type] = func
        return func
    return decorator

@register_handler("AttendanceMarkedEvent")
async def handle_attendance_marked(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        student_id = event.get("student_id")
        status = event.get("status")
        if status == "absent":
            await svc.send_from_template(
                template_name="attendance_absent",
                recipient_id=UUID(student_id),
                recipient_type="parent",
                variables={"date": event.get("date"), "status": status}
            )
        elif status == "late":
            await svc.send_from_template(
                template_name="attendance_late",
                recipient_id=UUID(student_id),
                recipient_type="parent",
                variables={"date": event.get("date")}
            )

@register_handler("PaymentReminder")  # from fee module
async def handle_payment_reminder(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        await svc.send_from_template(
            template_name="fee_reminder",
            recipient_id=UUID(event["student_id"]),
            recipient_type="parent",
            variables={"due_date": event.get("due_date")}
        )

@register_handler("ExamResultPublished")
async def handle_exam_result(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        await svc.send_from_template(
            template_name="exam_result",
            recipient_id=UUID(event["student_id"]),
            recipient_type="parent",
            variables={"exam_title": event.get("exam_title", "")}
        )

@register_handler("PerformanceDropAlert")
async def handle_performance_drop(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        await svc.send_from_template(
            template_name="performance_drop",
            recipient_id=UUID(event["student_id"]),
            recipient_type="parent",
            variables={"subject": event.get("subject_id", ""), "drop_percent": event.get("drop_percent", 0)}
        )

@register_handler("LeaveApprovedEvent")
async def handle_leave_approved(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        await svc.send_from_template(
            template_name="leave_approved",
            recipient_id=UUID(event["employee_id"]),
            recipient_type="staff",
            variables={"from_date": event.get("from_date"), "to_date": event.get("to_date")}
        )

async def consume_events():
    """Subscribe to all relevant channels and dispatch events to registered handlers."""
    pubsub = redis_client.pubsub()
    channels = ["attendance_events", "finance_events", "exam_events"]
    await pubsub.subscribe(*channels)
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            event = json.loads(message["data"])
            event_type = event.get("type")
            tenant_id = event.get("tenant_id")
            if event_type in EVENT_HANDLERS:
                await EVENT_HANDLERS[event_type](event, UUID(tenant_id))
        except Exception as e:
            # Log error
            print(f"Error processing event: {e}")
            

@register_handler("TransportBoardingEvent")
async def handle_transport_boarding(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        await svc.send_from_template("transport_boarding", UUID(event["student_id"]), "parent", {"time": event["timestamp"]})

@register_handler("HostelAbsentEvent")
async def handle_hostel_absent(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        await svc.send_from_template("hostel_absent", UUID(event["student_id"]), "parent", {})

@register_handler("MedicalAlert")
async def handle_medical_alert(event: dict, tenant_id: UUID):
    async with async_session_factory() as session:
        svc = NotificationService(session, tenant_id)
        await svc.send_from_template("medical_alert", UUID(event["student_id"]), "parent", {"details": event.get("details", "")})