import uuid
import sqlalchemy as sa
from sqlalchemy import Column, Date, Integer, Numeric, String, Text, Boolean, DateTime, JSON, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import EdVenturaBase

class Notification(EdVenturaBase):
    __tablename__ = "notifications"
    recipient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recipient_type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), default='medium')
    channel = Column(String(20), default='in_app')
    status = Column(String(20), default='sent')
    read_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    meta_data = Column(JSON, default={})
    is_moderated = Column(Boolean, default=False)
    moderated_by = Column(UUID(as_uuid=True), nullable=True)

class NotificationTemplate(EdVenturaBase):
    __tablename__ = "notification_templates"
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    title_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)
    default_priority = Column(String(20), default='medium')
    default_channels = Column(JSON, default=['in_app'])
    is_active = Column(Boolean, default=True)

class CommunicationPreference(EdVenturaBase):
    __tablename__ = "communication_preferences"
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'user_type', 'tenant_id', name='uq_comm_pref_user'),
    )
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_type = Column(String(20), nullable=False)
    channel_preferences = Column(JSON, default={})
    digest_enabled = Column(Boolean, default=True)
    digest_frequency = Column(String(20), default='daily')
    quiet_hours_start = Column(Time, nullable=True)
    quiet_hours_end = Column(Time, nullable=True)
    language = Column(String(10), nullable=True, default='en')
    
class CommunicationAuditLog(EdVenturaBase):
    __tablename__ = "communication_audit_log"
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=True)
    action = Column(String(50), nullable=False)
    performed_by = Column(UUID(as_uuid=True), nullable=False)
    details = Column(JSON, default={})
    performed_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    


class DirectMessage(EdVenturaBase):
    __tablename__ = "direct_messages"
    sender_id = Column(UUID(as_uuid=True), nullable=False)
    sender_role = Column(String(20), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), nullable=False)
    receiver_role = Column(String(20), nullable=False)
    subject = Column(String(200))
    body = Column(Text, nullable=False)
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("direct_messages.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), default='normal')
    is_moderated = Column(Boolean, default=False)
    moderated_by = Column(UUID(as_uuid=True), nullable=True)

class MessageAttachment(EdVenturaBase):
    __tablename__ = "message_attachments"
    message_type = Column(String(20), nullable=False)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100))
    file_size = Column(Integer)

class BroadcastList(EdVenturaBase):
    __tablename__ = "broadcast_lists"
    name = Column(String(100), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    roles = Column(JSON, default=[])
    created_by = Column(UUID(as_uuid=True), nullable=False)

class ScheduledMessage(EdVenturaBase):
    __tablename__ = "scheduled_messages"
    name = Column(String(200))
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"), nullable=True)
    recipient_query = Column(JSON, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    repeat_interval = Column(String(20), nullable=True)
    status = Column(String(20), default='pending')
    created_by = Column(UUID(as_uuid=True), nullable=False)

class EscalationRule(EdVenturaBase):
    __tablename__ = "escalation_rules"
    category = Column(String(50), nullable=False)
    timeout_minutes = Column(Integer, default=60)
    escalate_to_role = Column(String(20), nullable=False)
    channels = Column(JSON, default=['sms'])
    is_active = Column(Boolean, default=True)

class TemplateTranslation(EdVenturaBase):
    __tablename__ = "template_translations"
    __table_args__ = (
        sa.UniqueConstraint('template_id', 'language_code', 'tenant_id', name='uq_template_lang'),
    )
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"), nullable=False)
    language_code = Column(String(10), nullable=False)
    title_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)

class CommunicationAnalytics(EdVenturaBase):
    __tablename__ = "communication_analytics"
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_type = Column(String(20), nullable=False)
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_read = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    avg_response_time_minutes = Column(Numeric(10,2), default=0)
    reputation_score = Column(Numeric(5,2), default=100)


class BulletinBoardPost(EdVenturaBase):
    __tablename__ = "bulletin_board_posts"
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    target_audience = Column(JSON, default=[])
    pinned = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True))
    published_by = Column(UUID(as_uuid=True), nullable=False)
    attachments = Column(JSON, default=[])

class Meeting(EdVenturaBase):
    __tablename__ = "meetings"
    title = Column(String(200), nullable=False)
    description = Column(Text)
    meeting_type = Column(String(50), nullable=False)
    organizer_id = Column(UUID(as_uuid=True), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True))
    location = Column(String(200))
    meeting_link = Column(String(500))
    participants = Column(JSON, default=[])
    status = Column(String(20), default='scheduled')

class Survey(EdVenturaBase):
    __tablename__ = "surveys"
    title = Column(String(200), nullable=False)
    description = Column(Text)
    survey_type = Column(String(20), default='survey')
    questions = Column(JSON, nullable=False)
    target_audience = Column(JSON, default=[])
    is_anonymous = Column(Boolean, default=False)
    open_at = Column(DateTime(timezone=True))
    close_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), default='draft')

class SurveyResponse(EdVenturaBase):
    __tablename__ = "survey_responses"
    __table_args__ = (
        sa.UniqueConstraint('survey_id', 'respondent_id', 'tenant_id', name='uq_survey_respondent'),
    )
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.id"), nullable=False)
    respondent_id = Column(UUID(as_uuid=True), nullable=False)
    respondent_type = Column(String(20), nullable=False)
    answers = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class HomeworkReminder(EdVenturaBase):
    __tablename__ = "homework_reminders"
    student_id = Column(UUID(as_uuid=True), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), nullable=True)
    reminder_type = Column(String(30))
    sent_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class FeeReminderLog(EdVenturaBase):
    __tablename__ = "fee_reminder_logs"
    student_id = Column(UUID(as_uuid=True), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), nullable=True)
    reminder_stage = Column(Integer, default=1)
    sent_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    


class AIDraftLog(EdVenturaBase):
    __tablename__ = "ai_draft_logs"
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model = Column(String(50), nullable=False)
    tokens_used = Column(Integer)
    created_by = Column(UUID(as_uuid=True), nullable=False)

class AIOptimizationData(EdVenturaBase):
    __tablename__ = "ai_optimization_data"
    user_id = Column(UUID(as_uuid=True), nullable=False)
    best_send_hour = Column(Integer, nullable=True)
    best_channel = Column(String(20), nullable=True)
    avg_open_time_minutes = Column(Numeric(10,2))

class GrievanceTicket(EdVenturaBase):
    __tablename__ = "grievance_tickets"
    submitter_id = Column(UUID(as_uuid=True), nullable=False)
    submitter_type = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default='medium')
    status = Column(String(20), default='open')
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text)

class GrievanceComment(EdVenturaBase):
    __tablename__ = "grievance_comments"
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("grievance_tickets.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), nullable=False)
    author_type = Column(String(20), nullable=False)
    comment = Column(Text, nullable=False)

class ChatbotConversation(EdVenturaBase):
    __tablename__ = "chatbot_conversations"
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_type = Column(String(20), nullable=False)
    messages = Column(JSON, default=[])
    
    
class TutorBotSession(EdVenturaBase):
    __tablename__ = "tutorbot_sessions"
    student_id = Column(UUID(as_uuid=True), nullable=False)
    subject = Column(String(50), nullable=True)
    topic = Column(String(100), nullable=True)
    messages = Column(JSON, default=[])
    status = Column(String(20), default='active')
    

class CommunityGroup(EdVenturaBase):
    __tablename__ = "community_groups"
    name = Column(String(100), nullable=False)
    description = Column(Text)
    group_type = Column(String(30), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, default=True)

class CommunityGroupMember(EdVenturaBase):
    __tablename__ = "community_group_members"
    group_id = Column(UUID(as_uuid=True), ForeignKey("community_groups.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_type = Column(String(20), nullable=False)
    role = Column(String(20), default='member')

class CommunityEvent(EdVenturaBase):
    __tablename__ = "community_events"
    group_id = Column(UUID(as_uuid=True), ForeignKey("community_groups.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(30))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    location = Column(String(200))
    max_participants = Column(Integer)
    created_by = Column(UUID(as_uuid=True), nullable=False)

class EventRegistration(EdVenturaBase):
    __tablename__ = "event_registrations"
    event_id = Column(UUID(as_uuid=True), ForeignKey("community_events.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class AlumniRecord(EdVenturaBase):
    __tablename__ = "alumni_directory"
    student_id = Column(UUID(as_uuid=True), nullable=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    graduation_year = Column(Integer)
    current_profession = Column(String(100))
    opt_in_communication = Column(Boolean, default=True)

class AdmissionCampaign(EdVenturaBase):
    __tablename__ = "admission_campaigns"
    name = Column(String(100), nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    target_audience = Column(JSON, default=[])
    message_template = Column(Text)
    status = Column(String(20), default='draft')
    created_by = Column(UUID(as_uuid=True), nullable=False)

class AdmissionEnquiry(EdVenturaBase):
    __tablename__ = "admission_enquiries"
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("admission_campaigns.id"), nullable=True)
    prospect_name = Column(String(200), nullable=False)
    parent_name = Column(String(200))
    email = Column(String(255))
    phone = Column(String(20))
    student_grade = Column(String(20))
    status = Column(String(20), default='new')
    notes = Column(Text)

class ExternalWebhook(EdVenturaBase):
    __tablename__ = "external_webhooks"
    provider = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    secret_key = Column(String(200), nullable=False)
    event_types = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)

class CommunicationBranding(EdVenturaBase):
    __tablename__ = "communication_branding"
    tenant_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    sender_name = Column(String(100), nullable=False)
    sender_email = Column(String(255))
    logo_url = Column(String(500))
    primary_color = Column(String(7))
    footer_template = Column(Text)

class CommunicationLifecycle(EdVenturaBase):
    __tablename__ = "communication_lifecycles"
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    current_stage = Column(String(20), default='draft')
    submitted_by = Column(UUID(as_uuid=True))
    approved_by = Column(UUID(as_uuid=True))
    rejection_reason = Column(Text)

class OfflineSyncQueue(EdVenturaBase):
    __tablename__ = "offline_sync_queue"
    user_id = Column(UUID(as_uuid=True), nullable=False)
    message_type = Column(String(30), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default='pending')