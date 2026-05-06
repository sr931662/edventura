from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import date, datetime, time
from uuid import UUID

class NotificationOut(BaseModel):
    id: UUID
    recipient_id: UUID
    recipient_type: str
    title: str
    body: str
    category: str
    priority: str
    channel: str
    status: str
    read_at: Optional[datetime]
    delivered_at: Optional[datetime]
    meta_data: dict
    created_at: datetime
    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    recipient_id: UUID
    recipient_type: str = Field(..., pattern="^(student|parent|teacher|admin|staff|alumni)$")
    title: str
    body: str
    category: str
    priority: str = "medium"
    channel: str = "in_app"
    meta_data: Optional[dict] = {}
    recipient_email: Optional[EmailStr] = None  # skip DB lookup when caller already has the address

class TemplateCreate(BaseModel):
    name: str
    category: str
    title_template: str
    body_template: str
    default_priority: str = "medium"
    default_channels: List[str] = ["in_app"]

class TemplateOut(BaseModel):
    id: UUID
    name: str
    category: str
    title_template: str
    body_template: str
    default_priority: str
    default_channels: List[str]
    is_active: bool
    class Config:
        from_attributes = True

class PreferenceUpdate(BaseModel):
    channel_preferences: Optional[Dict[str, bool]] = None
    digest_enabled: Optional[bool] = None
    digest_frequency: Optional[str] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None

class PreferenceOut(BaseModel):
    user_id: UUID
    user_type: str
    channel_preferences: dict
    digest_enabled: bool
    digest_frequency: str
    quiet_hours_start: Optional[time]
    quiet_hours_end: Optional[time]
    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: UUID
    notification_id: Optional[UUID]
    action: str
    performed_by: UUID
    details: dict
    performed_at: datetime
    class Config:
        from_attributes = True
        
        
        
class DirectMessageCreate(BaseModel):
    receiver_id: UUID
    receiver_role: str = Field(..., pattern="^(parent|teacher|admin|staff|student)$")
    subject: Optional[str] = None
    body: str
    priority: str = "normal"
    attachments: Optional[List[UUID]] = None   # attachment IDs after upload

class DirectMessageOut(BaseModel):
    id: UUID
    sender_id: UUID
    sender_role: str
    receiver_id: UUID
    receiver_role: str
    subject: Optional[str]
    body: str
    is_read: bool
    read_at: Optional[datetime]
    priority: str
    created_at: datetime
    attachments: List[dict] = []
    class Config: from_attributes = True

class BroadcastCreate(BaseModel):
    name: str
    target_type: str = Field(..., pattern="^(all|class|section|role|custom)$")
    target_id: Optional[UUID] = None
    roles: Optional[List[str]] = []
    template_name: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    priority: str = "medium"
    channels: List[str] = ["in_app"]

class BroadcastOut(BaseModel):
    id: UUID
    name: str
    target_type: str
    recipient_count: int
    sent_at: datetime
    status: str

class ScheduleCreate(BaseModel):
    name: str
    template_name: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    target_type: str = Field(..., pattern="^(all|class|section|role)$")
    target_id: Optional[UUID] = None
    roles: Optional[List[str]] = []
    scheduled_at: datetime
    repeat_interval: Optional[str] = None

class ScheduleOut(BaseModel):
    id: UUID
    name: str
    scheduled_at: datetime
    repeat_interval: Optional[str]
    status: str
    class Config: from_attributes = True

class AttachmentUpload(BaseModel):
    file_name: str
    file_path: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None

class EscalationRuleCreate(BaseModel):
    category: str
    timeout_minutes: int = 60
    escalate_to_role: str
    channels: List[str] = ['sms']

class EscalationRuleOut(BaseModel):
    id: UUID
    category: str
    timeout_minutes: int
    escalate_to_role: str
    channels: List[str]
    is_active: bool

class TranslationCreate(BaseModel):
    template_id: UUID
    language_code: str
    title_template: str
    body_template: str

class TranslationOut(BaseModel):
    id: UUID
    template_id: UUID
    language_code: str
    title_template: str
    body_template: str

class AnalyticsOut(BaseModel):
    user_id: UUID
    user_type: str
    total_sent: int
    total_read: int
    read_rate: float
    reputation_score: float
    avg_response_time_minutes: float
    
# Bulletin / Circular / Notice
class BulletinCreate(BaseModel):
    title: str
    body: str
    category: str = Field(..., pattern="^(announcement|circular|memo|notice|event)$")
    target_audience: Optional[List[dict]] = []
    pinned: bool = False
    expires_at: Optional[datetime] = None

class BulletinOut(BaseModel):
    id: UUID
    title: str
    body: str
    category: str
    pinned: bool
    published_at: Optional[datetime]
    published_by: UUID
    expires_at: Optional[datetime]
    class Config: from_attributes = True

# Meeting
class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    meeting_type: str = Field(..., pattern="^(ptm|staff|interview|event|committee)$")
    scheduled_at: datetime
    end_at: Optional[datetime] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    participants: Optional[List[dict]] = []   # [{user_id, user_type}]

class MeetingOut(BaseModel):
    id: UUID
    title: str
    meeting_type: str
    organizer_id: UUID
    scheduled_at: datetime
    end_at: Optional[datetime]
    location: Optional[str]
    meeting_link: Optional[str]
    participants: List[dict]
    status: str
    class Config: from_attributes = True

class MeetingInviteResponse(BaseModel):
    status: str = Field(..., pattern="^(confirmed|declined)$")

# Survey / Poll
class SurveyQuestion(BaseModel):
    question_text: str
    question_type: str = Field(..., pattern="^(text|multiple_choice|single_choice|rating|yes_no)$")
    options: Optional[List[str]] = []

class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    survey_type: str = "survey"
    questions: List[SurveyQuestion]
    target_audience: Optional[List[dict]] = []
    is_anonymous: bool = False
    open_at: Optional[datetime] = None
    close_at: Optional[datetime] = None

class SurveyOut(BaseModel):
    id: UUID
    title: str
    survey_type: str
    questions: List[SurveyQuestion]
    is_anonymous: bool
    status: str
    total_responses: int = 0
    class Config: from_attributes = True

class SurveyAnswer(BaseModel):
    question_index: int
    answer: str

class SurveyResponseCreate(BaseModel):
    answers: List[SurveyAnswer]

class SurveyResponseOut(BaseModel):
    id: UUID
    survey_id: UUID
    respondent_id: UUID
    answers: List[dict]
    submitted_at: datetime
    
    
class AIDraftRequest(BaseModel):
    context_type: str   # announcement, reminder, feedback, etc.
    audience: str       # parents, students, staff
    key_points: List[str] = []
    tone: str = "professional"   # professional, friendly, urgent, casual

class AIDraftOut(BaseModel):
    title: str
    body: str
    model: str
    tokens_used: Optional[int]

class AIOptimizationOut(BaseModel):
    user_id: UUID
    best_send_hour: Optional[int]
    best_channel: Optional[str]
    avg_open_time_minutes: Optional[float]

class ChatbotRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None

class ChatbotResponse(BaseModel):
    reply: str
    conversation_id: UUID

class GrievanceCreate(BaseModel):
    category: str = Field(..., pattern="^(academic|administrative|finance|infrastructure|behavioral|other)$")
    subject: str
    description: str
    priority: str = "medium"

class GrievanceOut(BaseModel):
    id: UUID
    submitter_id: UUID
    category: str
    subject: str
    description: str
    priority: str
    status: str
    created_at: datetime
    comments_count: int = 0
    class Config: from_attributes = True

class GrievanceCommentCreate(BaseModel):
    comment: str

class GrievanceCommentOut(BaseModel):
    id: UUID
    author_id: UUID
    author_type: str
    comment: str
    created_at: datetime
    
    
class TutorBotAskRequest(BaseModel):
    message: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    session_id: Optional[UUID] = None   # existing session to continue

class TutorBotResponse(BaseModel):
    reply: str
    session_id: UUID

class TutorBotSessionOut(BaseModel):
    id: UUID
    subject: Optional[str]
    topic: Optional[str]
    created_at: datetime
    messages: List[dict]
    
class CommunityGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    group_type: str = Field(..., pattern="^(club|committee|house|team)$")

class CommunityGroupOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    group_type: str
    is_active: bool
    member_count: int = 0
    class Config: from_attributes = True

class CommunityEventCreate(BaseModel):
    group_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    max_participants: Optional[int] = None

class CommunityEventOut(BaseModel):
    id: UUID
    group_id: Optional[UUID]
    title: str
    description: Optional[str]
    event_type: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    registered_count: int = 0
    class Config: from_attributes = True

class AlumniCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    graduation_year: Optional[int] = None
    current_profession: Optional[str] = None

class AlumniOut(BaseModel):
    id: UUID
    full_name: str
    graduation_year: Optional[int]
    current_profession: Optional[str]
    opt_in_communication: bool

class AdmissionCampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    target_audience: Optional[List[dict]] = []
    message_template: Optional[str] = None

class AdmissionCampaignOut(BaseModel):
    id: UUID
    name: str
    start_date: date
    end_date: date
    status: str
    enquiries_count: int = 0

class AdmissionEnquiryCreate(BaseModel):
    campaign_id: Optional[UUID] = None
    prospect_name: str
    parent_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    student_grade: Optional[str] = None

class AdmissionEnquiryOut(BaseModel):
    id: UUID
    prospect_name: str
    phone: Optional[str]
    student_grade: Optional[str]
    status: str

class ExternalWebhookCreate(BaseModel):
    provider: str
    url: str
    secret_key: str
    event_types: List[str] = []

class ExternalWebhookOut(BaseModel):
    id: UUID
    provider: str
    event_types: List[str]
    is_active: bool
    
class BrandingCreate(BaseModel):
    sender_name: str
    sender_email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    footer_template: Optional[str] = None

class BrandingOut(BaseModel):
    id: UUID
    sender_name: str
    sender_email: Optional[str]
    logo_url: Optional[str]
    primary_color: Optional[str]
    footer_template: Optional[str]
    class Config: from_attributes = True

class LifecycleCreate(BaseModel):
    entity_type: str
    entity_id: UUID

class LifecycleOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    current_stage: str
    submitted_by: Optional[UUID]
    approved_by: Optional[UUID]
    class Config: from_attributes = True

class OfflineSyncPayload(BaseModel):
    message_type: str
    payload: dict

class ModerationAction(BaseModel):
    action: str = Field(..., pattern="^(approve|flag)$")  # approve or flag
    reason: Optional[str] = None