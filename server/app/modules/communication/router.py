from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_tenant
from app.core.permissions import PermissionChecker
from app.models.communication_models import EscalationRule
from app.models.user import User
from app.modules.communication.services.analytics_service import CommunicationAnalyticsService
from app.modules.communication.services.broadcast_service import BroadcastService
from app.modules.communication.services.escalation_service import EscalationService
from app.modules.communication.services.language_service import LanguageService
from app.modules.communication.services.messaging_service import MessagingService
from app.modules.communication.services.notification_service import NotificationService
from app.modules.communication.services.scheduled_service import ScheduledService
from app.modules.communication.services.template_service import TemplateService
from app.modules.communication.services.preference_service import PreferenceService
from app.modules.communication import schemas

from app.modules.communication.services.bulletin_service import BulletinService
from app.modules.communication.services.meeting_service import MeetingService
from app.modules.communication.services.survey_service import SurveyService
from app.modules.communication.services.domain_reminders import DomainReminderService

from app.modules.communication.services.ai_drafting_service import AIDraftingService
from app.modules.communication.services.ai_optimization_service import AIOptimizationService
from app.modules.communication.services.ai_chatbot_service import AIChatbotService
from app.modules.communication.services.grievance_service import GrievanceService

from app.modules.communication.services.tutorbot_service import TutorBotService

from app.modules.communication.services.community_service import CommunityService
from app.modules.communication.services.alumni_service import AlumniService
from app.modules.communication.services.admission_service import AdmissionService
from app.modules.communication.services.webhook_service import WebhookService

from app.modules.communication.services.branding_service import CommunicationBrandingService
from app.modules.communication.services.lifecycle_service import LifecycleService
from app.modules.communication.services.offline_sync_service import OfflineSyncService
from app.modules.communication.services.moderation_service import ModerationService
from app.modules.communication.services.feature_gating import CommunicationFeatureGate

router = APIRouter(prefix="/communications", tags=["Communication"])

async def get_ai_drafting_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AIDraftingService:
    return AIDraftingService(db, UUID(tenant_id))

async def get_ai_optimization_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AIOptimizationService:
    return AIOptimizationService(db, UUID(tenant_id))

async def get_ai_chatbot_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AIChatbotService:
    return AIChatbotService(db, UUID(tenant_id))

async def get_grievance_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> GrievanceService:
    return GrievanceService(db, UUID(tenant_id))
async def get_broadcast_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> BroadcastService:
    return BroadcastService(db, UUID(tenant_id))
async def get_messaging_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> MessagingService:
    return MessagingService(db, UUID(tenant_id))
async def get_scheduled_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ScheduledService:
    return ScheduledService(db, UUID(tenant_id))

async def get_escalation_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> EscalationService:
    return EscalationService(db, UUID(tenant_id))

async def get_language_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> LanguageService:
    return LanguageService(db, UUID(tenant_id))

async def get_analytics_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> CommunicationAnalyticsService:
    return CommunicationAnalyticsService(db, UUID(tenant_id))

async def get_notification_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> NotificationService:
    return NotificationService(db, UUID(tenant_id))

async def get_template_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> TemplateService:
    return TemplateService(db, UUID(tenant_id))

async def get_preference_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> PreferenceService:
    return PreferenceService(db, UUID(tenant_id))


async def get_bulletin_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> BulletinService:
    return BulletinService(db, UUID(tenant_id))

async def get_meeting_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> MeetingService:
    return MeetingService(db, UUID(tenant_id))

async def get_survey_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> SurveyService:
    return SurveyService(db, UUID(tenant_id))

async def get_domain_reminder_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> DomainReminderService:
    return DomainReminderService(db, UUID(tenant_id))

async def get_tutorbot_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> TutorBotService:
    return TutorBotService(db, UUID(tenant_id))

async def get_community_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> CommunityService:
    return CommunityService(db, UUID(tenant_id))

async def get_alumni_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AlumniService:
    return AlumniService(db, UUID(tenant_id))

async def get_admission_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AdmissionService:
    return AdmissionService(db, UUID(tenant_id))

async def get_webhook_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> WebhookService:
    return WebhookService(db, UUID(tenant_id))

async def get_comm_branding_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> CommunicationBrandingService:
    return CommunicationBrandingService(db, UUID(tenant_id))

async def get_lifecycle_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> LifecycleService:
    return LifecycleService(db, UUID(tenant_id))

async def get_offline_sync_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> OfflineSyncService:
    return OfflineSyncService(db, UUID(tenant_id))

async def get_moderation_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ModerationService:
    return ModerationService(db, UUID(tenant_id))

async def get_comm_feature_gate(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> CommunicationFeatureGate:
    return CommunicationFeatureGate(db, UUID(tenant_id))

# ---------- Notifications ----------
@router.post("/send", response_model=schemas.NotificationOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_notification(data: schemas.NotificationCreate, svc: NotificationService = Depends(get_notification_service)):
    return await svc.send_notification(data)

@router.get("/inbox", response_model=List[schemas.NotificationOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def inbox(skip: int = 0, limit: int = 50,
                current_user: User = Depends(get_current_user),
                svc: NotificationService = Depends(get_notification_service)):
    return await svc.get_inbox(current_user.id, skip, limit)

@router.post("/{notification_id}/read", dependencies=[Depends(PermissionChecker("communication:read"))])
async def mark_read(notification_id: UUID,
                    current_user: User = Depends(get_current_user),
                    svc: NotificationService = Depends(get_notification_service)):
    notif = await svc.mark_read(notification_id, current_user.id)
    if not notif:
        raise HTTPException(404, "Notification not found")
    return {"status": "read"}

@router.get("/unread-count", response_model=int, dependencies=[Depends(PermissionChecker("communication:read"))])
async def unread_count(current_user: User = Depends(get_current_user),
                       svc: NotificationService = Depends(get_notification_service)):
    return await svc.get_unread_count(current_user.id)

# ---------- Templates ----------
@router.post("/templates", response_model=schemas.TemplateOut, dependencies=[Depends(PermissionChecker("communication:write"))])
async def create_template(data: schemas.TemplateCreate, svc: TemplateService = Depends(get_template_service)):
    return await svc.create_template(data.dict())

@router.put("/templates/{template_id}", response_model=schemas.TemplateOut, dependencies=[Depends(PermissionChecker("communication:write"))])
async def update_template(template_id: UUID, data: schemas.TemplateCreate, svc: TemplateService = Depends(get_template_service)):
    tpl = await svc.update_template(template_id, data.dict(exclude_unset=True))
    if not tpl:
        raise HTTPException(404, "Template not found")
    return tpl

@router.get("/templates", response_model=List[schemas.TemplateOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_templates(category: Optional[str] = None, svc: TemplateService = Depends(get_template_service)):
    return await svc.list_templates(category)

@router.delete("/templates/{template_id}", status_code=204, dependencies=[Depends(PermissionChecker("communication:write"))])
async def delete_template(template_id: UUID, svc: TemplateService = Depends(get_template_service)):
    if not await svc.delete_template(template_id):
        raise HTTPException(404, "Template not found")

# ---------- Preferences ----------
@router.get("/preferences", response_model=schemas.PreferenceOut, dependencies=[Depends(PermissionChecker("communication:read"))])
async def get_preferences(current_user: User = Depends(get_current_user),
                          svc: PreferenceService = Depends(get_preference_service)):
    return await svc.get_preferences(current_user.id, current_user.role or "teacher")  # use actual role

@router.put("/preferences", response_model=schemas.PreferenceOut, dependencies=[Depends(PermissionChecker("communication:write"))])
async def update_preferences(data: schemas.PreferenceUpdate,
                             current_user: User = Depends(get_current_user),
                             svc: PreferenceService = Depends(get_preference_service)):
    return await svc.update_preferences(current_user.id, current_user.role or "teacher", data.dict(exclude_unset=True))



# Broadcast
@router.post("/broadcast", dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_broadcast(data: schemas.BroadcastCreate, current_user: User = Depends(get_current_user),
                         svc: BroadcastService = Depends(get_broadcast_service)):
    return await svc.send_broadcast(data, current_user.id)

# Direct Messaging
@router.post("/messages", response_model=schemas.DirectMessageOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_message(data: schemas.DirectMessageCreate, current_user: User = Depends(get_current_user),
                       svc: MessagingService = Depends(get_messaging_service)):
    return await svc.send_message(data, current_user.id, "teacher")  # real role from user

@router.get("/messages/conversation/{other_user_id}", response_model=List[schemas.DirectMessageOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def conversation(other_user_id: UUID, skip: int = 0, limit: int = 50,
                      current_user: User = Depends(get_current_user),
                      svc: MessagingService = Depends(get_messaging_service)):
    return await svc.get_conversation(current_user.id, other_user_id, skip, limit)

@router.post("/messages/{message_id}/read", dependencies=[Depends(PermissionChecker("communication:read"))])
async def mark_message_read(message_id: UUID, current_user: User = Depends(get_current_user),
                           svc: MessagingService = Depends(get_messaging_service)):
    await svc.mark_read(message_id, current_user.id)
    return {"status": "read"}

@router.post("/attachments/upload")
async def upload_attachment(file: UploadFile = File(...), svc: MessagingService = Depends(get_messaging_service)):
    content = await file.read()
    att = await svc.upload_attachment(content, file.filename, file.content_type)
    return {"attachment_id": str(att.id), "file_name": att.file_name}

# Scheduled Messages
@router.post("/schedules", response_model=schemas.ScheduleOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def schedule_message(data: schemas.ScheduleCreate, current_user: User = Depends(get_current_user),
                           svc: ScheduledService = Depends(get_scheduled_service)):
    return await svc.schedule_message(data.dict(), current_user.id)

# Escalation Rules
@router.post("/escalation-rules", response_model=schemas.EscalationRuleOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def create_escalation_rule(data: schemas.EscalationRuleCreate, svc: EscalationService = Depends(get_escalation_service)):
    rule = EscalationRule(tenant_id=..., **data.dict())
    svc.db.add(rule)
    await svc.db.commit()
    return rule

@router.get("/escalation-rules", response_model=List[schemas.EscalationRuleOut], dependencies=[Depends(PermissionChecker("communication:admin"))])
async def list_escalation_rules(svc: EscalationService = Depends(get_escalation_service)):
    return (await svc.db.execute(select(EscalationRule).where(EscalationRule.tenant_id == svc.tenant_id))).scalars().all()

# Multi‑Language
@router.post("/translations", response_model=schemas.TranslationOut, dependencies=[Depends(PermissionChecker("communication:write"))])
async def add_translation(data: schemas.TranslationCreate, svc: LanguageService = Depends(get_language_service)):
    return await svc.add_translation(data.dict())

# Analytics
@router.get("/analytics/{user_id}", response_model=schemas.AnalyticsOut, dependencies=[Depends(PermissionChecker("communication:read"))])
async def get_analytics(user_id: UUID, svc: CommunicationAnalyticsService = Depends(get_analytics_service)):
    analytics = await svc.get_analytics(user_id)
    if not analytics:
        raise HTTPException(404, "Analytics not found")
    return analytics




# ---------- Bulletin Board ----------
@router.post("/bulletins", response_model=schemas.BulletinOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def publish_bulletin(data: schemas.BulletinCreate, current_user: User = Depends(get_current_user),
                           svc: BulletinService = Depends(get_bulletin_service)):
    return await svc.publish(data, current_user.id)

@router.get("/bulletins", response_model=List[schemas.BulletinOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_bulletins(category: Optional[str] = None, skip: int = 0, limit: int = 20,
                         svc: BulletinService = Depends(get_bulletin_service)):
    return await svc.get_active_posts(category, skip, limit)

# ---------- Meetings ----------
@router.post("/meetings", response_model=schemas.MeetingOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def schedule_meeting(data: schemas.MeetingCreate, current_user: User = Depends(get_current_user),
                           svc: MeetingService = Depends(get_meeting_service)):
    return await svc.schedule_meeting(data, current_user.id)

@router.put("/meetings/{meeting_id}/respond", response_model=schemas.MeetingOut, dependencies=[Depends(PermissionChecker("communication:read"))])
async def respond_meeting(meeting_id: UUID, response: schemas.MeetingInviteResponse,
                          current_user: User = Depends(get_current_user),
                          svc: MeetingService = Depends(get_meeting_service)):
    meeting = await svc.respond_to_invite(meeting_id, current_user.id, response.status)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting

@router.get("/meetings/upcoming", response_model=List[schemas.MeetingOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def upcoming_meetings(current_user: User = Depends(get_current_user),
                            svc: MeetingService = Depends(get_meeting_service)):
    return await svc.get_upcoming_meetings(current_user.id)

# ---------- Surveys ----------
@router.post("/surveys", response_model=schemas.SurveyOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def create_survey(data: schemas.SurveyCreate, current_user: User = Depends(get_current_user),
                        svc: SurveyService = Depends(get_survey_service)):
    return await svc.create_survey(data, current_user.id)

@router.put("/surveys/{survey_id}/publish", response_model=schemas.SurveyOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def publish_survey(survey_id: UUID, svc: SurveyService = Depends(get_survey_service)):
    survey = await svc.publish_survey(survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found")
    return survey

@router.post("/surveys/{survey_id}/respond", dependencies=[Depends(PermissionChecker("communication:read"))])
async def respond_survey(survey_id: UUID, data: schemas.SurveyResponseCreate,
                         current_user: User = Depends(get_current_user),
                         svc: SurveyService = Depends(get_survey_service)):
    try:
        resp = await svc.submit_response(survey_id, current_user.id, "student", [a.dict() for a in data.answers])
        return {"response_id": str(resp.id)}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/surveys/{survey_id}/results", dependencies=[Depends(PermissionChecker("communication:read"))])
async def survey_results(survey_id: UUID, svc: SurveyService = Depends(get_survey_service)):
    return await svc.get_survey_results(survey_id)

# ---------- Domain Reminders (Manual Triggers – production uses events) ----------
@router.post("/reminders/homework", dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_homework_reminder(student_id: UUID, assignment_id: UUID, reminder_type: str = "pending",
                                 svc: DomainReminderService = Depends(get_domain_reminder_service)):
    await svc.send_homework_reminder(student_id, assignment_id, reminder_type)
    return {"status": "sent"}

@router.post("/reminders/fee", dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_fee_reminder(student_id: UUID, invoice_id: UUID, stage: int = 1,
                            svc: DomainReminderService = Depends(get_domain_reminder_service)):
    await svc.send_fee_reminder(student_id, invoice_id, stage)
    return {"status": "sent"}

@router.post("/reminders/exam", dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_exam_alert(student_id: UUID, exam_id: UUID, exam_title: str, schedule_date: str,
                          svc: DomainReminderService = Depends(get_domain_reminder_service)):
    await svc.send_exam_alert(student_id, exam_id, exam_title, schedule_date)
    return {"status": "sent"}

@router.post("/reminders/result", dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_result_notification(student_id: UUID, exam_title: str,
                                   svc: DomainReminderService = Depends(get_domain_reminder_service)):
    await svc.send_result_notification(student_id, exam_title)
    return {"status": "sent"}

@router.post("/reminders/milestone", dependencies=[Depends(PermissionChecker("communication:send"))])
async def send_milestone(student_id: UUID, milestone: str, details: str = "",
                         svc: DomainReminderService = Depends(get_domain_reminder_service)):
    await svc.send_milestone(student_id, milestone, details)
    return {"status": "sent"}



# ---------- AI Drafting ----------
@router.post("/ai/draft", response_model=schemas.AIDraftOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def ai_draft(data: schemas.AIDraftRequest, current_user: User = Depends(get_current_user),
                   svc: AIDraftingService = Depends(get_ai_drafting_service)):
    return await svc.draft_message(data, current_user.id)

# ---------- AI Optimization ----------
@router.get("/ai/optimization/{user_id}", response_model=schemas.AIOptimizationOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def get_optimization(user_id: UUID, svc: AIOptimizationService = Depends(get_ai_optimization_service)):
    data = await svc.compute_optimal_send_time(user_id)
    return data

# ---------- AI Chatbot ----------
@router.post("/ai/chatbot", response_model=schemas.ChatbotResponse, dependencies=[Depends(PermissionChecker("communication:read"))])
async def chatbot_chat(data: schemas.ChatbotRequest,
                       current_user: User = Depends(get_current_user),
                       svc: AIChatbotService = Depends(get_ai_chatbot_service)):
    return await svc.chat(data, current_user.id, "student")

# ---------- Grievance Tickets ----------
@router.post("/grievance", response_model=schemas.GrievanceOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def submit_grievance(data: schemas.GrievanceCreate,
                           current_user: User = Depends(get_current_user),
                           svc: GrievanceService = Depends(get_grievance_service)):
    ticket = await svc.create_ticket(data, current_user.id, "student")
    return ticket

@router.get("/grievance", response_model=List[schemas.GrievanceOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_my_grievances(current_user: User = Depends(get_current_user),
                             svc: GrievanceService = Depends(get_grievance_service)):
    tickets = await svc.list_user_tickets(current_user.id)
    # Get comments count
    result = []
    for t in tickets:
        result.append(schemas.GrievanceOut(
            id=t.id,
            submitter_id=t.submitter_id,
            category=t.category,
            subject=t.subject,
            description=t.description,
            priority=t.priority,
            status=t.status,
            created_at=t.created_at,
            comments_count=0  # can add aggregation
        ))
    return result

@router.get("/grievance/{ticket_id}", response_model=schemas.GrievanceOut, dependencies=[Depends(PermissionChecker("communication:read"))])
async def get_grievance(ticket_id: UUID, svc: GrievanceService = Depends(get_grievance_service)):
    ticket = await svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket

@router.post("/grievance/{ticket_id}/comment", response_model=schemas.GrievanceCommentOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def comment_on_grievance(ticket_id: UUID, data: schemas.GrievanceCommentCreate,
                               current_user: User = Depends(get_current_user),
                               svc: GrievanceService = Depends(get_grievance_service)):
    comment = await svc.add_comment(ticket_id, data.comment, current_user.id, "admin")
    return comment

@router.get("/grievance/{ticket_id}/comments", response_model=List[schemas.GrievanceCommentOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_grievance_comments(ticket_id: UUID, svc: GrievanceService = Depends(get_grievance_service)):
    return await svc.get_comments(ticket_id)


# ---------- TutorBot ----------
@router.post("/tutorbot/ask", response_model=schemas.TutorBotResponse, dependencies=[Depends(PermissionChecker("communication:read"))])
async def tutorbot_ask(
    data: schemas.TutorBotAskRequest,
    current_user: User = Depends(get_current_user),
    svc: TutorBotService = Depends(get_tutorbot_service)
):
    result = await svc.ask(
        student_id=current_user.id,
        message=data.message,
        subject=data.subject,
        topic=data.topic,
        session_id=data.session_id
    )
    return schemas.TutorBotResponse(
        reply=result["reply"],
        session_id=result["session_id"]
    )

@router.get("/tutorbot/sessions", response_model=List[schemas.TutorBotSessionOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def tutorbot_sessions(
    current_user: User = Depends(get_current_user),
    svc: TutorBotService = Depends(get_tutorbot_service)
):
    sessions = await svc.get_session_history(current_user.id)
    return [schemas.TutorBotSessionOut(
        id=s.id,
        subject=s.subject,
        topic=s.topic,
        created_at=s.created_at,
        messages=s.messages or []
    ) for s in sessions]

@router.put("/tutorbot/sessions/{session_id}/close", dependencies=[Depends(PermissionChecker("communication:read"))])
async def close_tutorbot_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    svc: TutorBotService = Depends(get_tutorbot_service)
):
    success = await svc.close_session(session_id, current_user.id)
    if not success:
        raise HTTPException(404, "Session not found or unauthorized")
    return {"status": "closed"}



# ---------- Community Groups ----------
@router.post("/community/groups", response_model=schemas.CommunityGroupOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def create_community_group(data: schemas.CommunityGroupCreate, current_user: User = Depends(get_current_user),
                                 svc: CommunityService = Depends(get_community_service)):
    return await svc.create_group(data.dict(), current_user.id)

@router.get("/community/groups", response_model=List[schemas.CommunityGroupOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_community_groups(group_type: Optional[str] = None, svc: CommunityService = Depends(get_community_service)):
    return await svc.list_groups(group_type)

@router.post("/community/groups/{group_id}/join", dependencies=[Depends(PermissionChecker("communication:read"))])
async def join_group(group_id: UUID, current_user: User = Depends(get_current_user),
                     svc: CommunityService = Depends(get_community_service)):
    await svc.join_group(group_id, current_user.id, "student")
    return {"status": "joined"}

# ---------- Community Events ----------
@router.post("/community/events", response_model=schemas.CommunityEventOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def create_community_event(data: schemas.CommunityEventCreate, current_user: User = Depends(get_current_user),
                                 svc: CommunityService = Depends(get_community_service)):
    return await svc.create_event(data.dict(), current_user.id)

@router.get("/community/events", response_model=List[schemas.CommunityEventOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_community_events(group_id: Optional[UUID] = None, svc: CommunityService = Depends(get_community_service)):
    return await svc.list_events(group_id)

@router.post("/community/events/{event_id}/register", dependencies=[Depends(PermissionChecker("communication:read"))])
async def register_for_event(event_id: UUID, current_user: User = Depends(get_current_user),
                             svc: CommunityService = Depends(get_community_service)):
    await svc.register_for_event(event_id, current_user.id)
    return {"status": "registered"}

# ---------- Alumni ----------
@router.post("/alumni", response_model=schemas.AlumniOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def add_alumnus(data: schemas.AlumniCreate, svc: AlumniService = Depends(get_alumni_service)):
    return await svc.add_alumnus(data.dict())

@router.get("/alumni", response_model=List[schemas.AlumniOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_alumni(graduation_year: Optional[int] = None, svc: AlumniService = Depends(get_alumni_service)):
    return await svc.list_alumni(graduation_year)

# ---------- Admission ----------
@router.post("/admission/campaigns", response_model=schemas.AdmissionCampaignOut, dependencies=[Depends(PermissionChecker("communication:send"))])
async def create_admission_campaign(data: schemas.AdmissionCampaignCreate, current_user: User = Depends(get_current_user),
                                    svc: AdmissionService = Depends(get_admission_service)):
    return await svc.create_campaign(data.dict(), current_user.id)

@router.get("/admission/campaigns", response_model=List[schemas.AdmissionCampaignOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_admission_campaigns(svc: AdmissionService = Depends(get_admission_service)):
    return await svc.list_campaigns()

@router.post("/admission/enquiries", response_model=schemas.AdmissionEnquiryOut, dependencies=[Depends(PermissionChecker("communication:read"))])  # public endpoint
async def submit_admission_enquiry(data: schemas.AdmissionEnquiryCreate, svc: AdmissionService = Depends(get_admission_service)):
    return await svc.submit_enquiry(data.dict())

@router.get("/admission/enquiries", response_model=List[schemas.AdmissionEnquiryOut], dependencies=[Depends(PermissionChecker("communication:read"))])
async def list_admission_enquiries(campaign_id: Optional[UUID] = None, svc: AdmissionService = Depends(get_admission_service)):
    return await svc.list_enquiries(campaign_id)

# ---------- External Webhooks ----------
@router.post("/webhooks", response_model=schemas.ExternalWebhookOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def register_webhook(data: schemas.ExternalWebhookCreate, svc: WebhookService = Depends(get_webhook_service)):
    return await svc.register_webhook(data.dict())



# ---------- Branding ----------
@router.get("/branding", response_model=schemas.BrandingOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def get_communication_branding(svc: CommunicationBrandingService = Depends(get_comm_branding_service)):
    branding = await svc.get_branding()
    if not branding:
        raise HTTPException(404, "Communication branding not configured")
    return branding

@router.put("/branding", response_model=schemas.BrandingOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def update_communication_branding(data: schemas.BrandingCreate, svc: CommunicationBrandingService = Depends(get_comm_branding_service)):
    return await svc.upsert_branding(data.dict())

# ---------- Lifecycle Management ----------
@router.post("/lifecycle", response_model=schemas.LifecycleOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def create_lifecycle(data: schemas.LifecycleCreate, current_user: User = Depends(get_current_user),
                           svc: LifecycleService = Depends(get_lifecycle_service)):
    return await svc.create(data.entity_type, data.entity_id, current_user.id)

@router.put("/lifecycle/{lifecycle_id}/submit", response_model=schemas.LifecycleOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def submit_lifecycle(lifecycle_id: UUID, current_user: User = Depends(get_current_user),
                           svc: LifecycleService = Depends(get_lifecycle_service)):
    lc = await svc.submit_for_approval(lifecycle_id, current_user.id)
    if not lc: raise HTTPException(404, "Lifecycle not found")
    return lc

@router.put("/lifecycle/{lifecycle_id}/approve", response_model=schemas.LifecycleOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def approve_lifecycle(lifecycle_id: UUID, current_user: User = Depends(get_current_user),
                            svc: LifecycleService = Depends(get_lifecycle_service)):
    lc = await svc.approve(lifecycle_id, current_user.id)
    if not lc: raise HTTPException(404, "Lifecycle not found")
    return lc

@router.put("/lifecycle/{lifecycle_id}/publish", response_model=schemas.LifecycleOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def publish_lifecycle(lifecycle_id: UUID, svc: LifecycleService = Depends(get_lifecycle_service)):
    lc = await svc.publish(lifecycle_id)
    if not lc: raise HTTPException(400, "Cannot publish; not approved")
    return lc

@router.put("/lifecycle/{lifecycle_id}/archive", response_model=schemas.LifecycleOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def archive_lifecycle(lifecycle_id: UUID, svc: LifecycleService = Depends(get_lifecycle_service)):
    lc = await svc.archive(lifecycle_id)
    if not lc: raise HTTPException(404, "Lifecycle not found")
    return lc

@router.put("/lifecycle/{lifecycle_id}/reject", response_model=schemas.LifecycleOut, dependencies=[Depends(PermissionChecker("communication:admin"))])
async def reject_lifecycle(lifecycle_id: UUID, reason: str = Query(...), current_user: User = Depends(get_current_user),
                           svc: LifecycleService = Depends(get_lifecycle_service)):
    lc = await svc.reject(lifecycle_id, reason, current_user.id)
    if not lc: raise HTTPException(404, "Lifecycle not found")
    return lc

# ---------- Offline Sync ----------
@router.post("/offline/enqueue", dependencies=[Depends(PermissionChecker("communication:send"))])
async def enqueue_offline(data: schemas.OfflineSyncPayload, current_user: User = Depends(get_current_user),
                          svc: OfflineSyncService = Depends(get_offline_sync_service)):
    await svc.enqueue(current_user.id, data.message_type, data.payload)
    return {"status": "queued"}

@router.get("/offline/pending", response_model=List[dict], dependencies=[Depends(PermissionChecker("communication:read"))])
async def get_pending_offline(current_user: User = Depends(get_current_user),
                              svc: OfflineSyncService = Depends(get_offline_sync_service)):
    items = await svc.get_pending_for_user(current_user.id)
    return [{"id": str(i.id), "message_type": i.message_type, "payload": i.payload, "status": i.status} for i in items]

@router.put("/offline/{queue_id}/synced", dependencies=[Depends(PermissionChecker("communication:read"))])
async def mark_offline_synced(queue_id: UUID, svc: OfflineSyncService = Depends(get_offline_sync_service)):
    await svc.mark_synced(queue_id)
    return {"status": "synced"}

# ---------- Moderation ----------
@router.put("/moderate/{message_type}/{message_id}", dependencies=[Depends(PermissionChecker("communication:admin"))])
async def moderate_message(message_type: str, message_id: UUID, action: schemas.ModerationAction,
                           current_user: User = Depends(get_current_user),
                           svc: ModerationService = Depends(get_moderation_service)):
    success = await svc.moderate_message(message_type, message_id, action.action, current_user.id, action.reason)
    if not success:
        raise HTTPException(404, "Message not found")
    return {"status": "moderated"}

# ---------- Feature Gate Toggle ----------
@router.get("/features/list", response_model=List[dict], dependencies=[Depends(PermissionChecker("system:read"))])
async def list_comm_features(svc: CommunicationFeatureGate = Depends(get_comm_feature_gate)):
    return [{"feature": "ai_drafting", "enabled": await svc.is_enabled("ai_drafting")},
            {"feature": "chatbot", "enabled": await svc.is_enabled("chatbot")},
            {"feature": "broadcast", "enabled": await svc.is_enabled("broadcast")}]

@router.post("/features/toggle", dependencies=[Depends(PermissionChecker("system:write"))])
async def toggle_comm_feature(feature_name: str, enabled: bool, svc: CommunicationFeatureGate = Depends(get_comm_feature_gate)):
    gate = await svc.set_feature(feature_name, enabled)
    return {"feature": gate.feature_name, "enabled": gate.enabled}