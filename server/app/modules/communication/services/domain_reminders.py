from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.communication_models import HomeworkReminder, FeeReminderLog
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.schemas import NotificationCreate
from datetime import datetime, timedelta

class DomainReminderService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.notif_svc = NotificationService(db, tenant_id)

    # ---------- Homework Reminders ----------
    async def send_homework_reminder(self, student_id: UUID, assignment_id: UUID, reminder_type: str):
        await self.notif_svc.send_from_template(
            f"homework_{reminder_type}",
            student_id, "student",
            {}
        )
        self.db.add(HomeworkReminder(
            tenant_id=self.tenant_id,
            student_id=student_id,
            assignment_id=assignment_id,
            reminder_type=reminder_type
        ))
        await self.db.commit()

    # ---------- Fee Reminders (called by Celery or event) ----------
    async def send_fee_reminder(self, student_id: UUID, invoice_id: UUID, stage: int):
        await self.notif_svc.send_from_template(
            "fee_reminder",
            student_id, "parent",
            {"stage": stage}
        )
        self.db.add(FeeReminderLog(
            tenant_id=self.tenant_id,
            student_id=student_id,
            invoice_id=invoice_id,
            reminder_stage=stage
        ))
        await self.db.commit()

    # ---------- Exam Alerts ----------
    async def send_exam_alert(self, student_id: UUID, exam_id: UUID, exam_title: str, schedule_date: str):
        await self.notif_svc.send_from_template(
            "exam_schedule",
            student_id, "student",
            {"exam_title": exam_title, "date": schedule_date}
        )

    async def send_result_notification(self, student_id: UUID, exam_title: str):
        await self.notif_svc.send_from_template(
            "exam_result",
            student_id, "parent",
            {"exam_title": exam_title}
        )

    # ---------- Leave Notifications ----------
    async def send_leave_decision(self, employee_id: UUID, status: str, from_date: str, to_date: str):
        template = "leave_approved" if status == "approved" else "leave_rejected"
        await self.notif_svc.send_from_template(
            template,
            employee_id, "staff",
            {"from_date": from_date, "to_date": to_date}
        )

    # ---------- Academic Milestones ----------
    async def send_milestone(self, student_id: UUID, milestone: str, details: str = ""):
        await self.notif_svc.send_notification(NotificationCreate(
            recipient_id=student_id,
            recipient_type="student",
            title=f"🎉 Achievement: {milestone}",
            body=details,
            category="milestone",
            priority="medium",
            channel="in_app"
        ))