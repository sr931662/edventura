from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.communication_models import NotificationTemplate


async def seed_communication_templates():
    async with async_session_factory() as session:
        templates = [
            ("attendance_absent", "attendance", "Absent Today", "Your child was marked absent on {{ date }}."),
            ("attendance_late", "attendance", "Late Arrival", "Your child arrived late on {{ date }}."),
            ("fee_reminder", "fee", "Fee Payment Reminder", "Fee is due by {{ due_date }}. Please pay soon."),
            ("exam_result", "exam", "Exam Results Available", "Results for {{ exam_title }} are now published."),
            ("performance_drop", "exam", "Performance Alert", "Performance dropped by {{ drop_percent }}% in {{ subject }}."),
            ("leave_approved", "hr", "Leave Approved", "Your leave from {{ from_date }} to {{ to_date }} is approved."),
        ]
        for name, category, title, body in templates:
            existing = await session.execute(select(NotificationTemplate).where(NotificationTemplate.name == name).limit(1))
            if not existing.scalar_one_or_none():
                session.add(NotificationTemplate(
                    tenant_id=...,  # default tenant
                    name=name, category=category,
                    title_template=title, body_template=body,
                    default_channels=["in_app"]
                ))
        await session.commit()