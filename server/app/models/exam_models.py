import uuid
from sqlalchemy import Column, Date, String, Text, Integer, Numeric, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import EdVenturaBase
from app.core.database import Base
import hashlib
import sqlalchemy as sa

class Subject(EdVenturaBase):
    __tablename__ = "subjects"
    name = Column(String(100), nullable=False)
    code = Column(String(20))
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class Topic(EdVenturaBase):
    __tablename__ = "topics"
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class Question(EdVenturaBase):
    __tablename__ = "question_bank"
    __table_args__ = (
        sa.UniqueConstraint('tenant_id', 'content_hash', name='uq_question_hash_tenant'),
    )
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    question_type = Column(String(20), nullable=False)  # mcq, subjective, true_false, fill_blank
    difficulty = Column(String(20), default='medium')
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    correct_answer = Column(Text, nullable=True)
    marks = Column(Integer, default=1)
    negative_marks = Column(Numeric(5,2), default=0)
    bloom_level = Column(String(20))
    tags = Column(JSON, default=[])
    version = Column(Integer, default=1)
    content_hash = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

class ExamTemplate(EdVenturaBase):
    __tablename__ = "exam_templates"
    name = Column(String(100), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    blueprint = Column(JSON, nullable=False)
    duration_minutes = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

class Exam(EdVenturaBase):
    __tablename__ = "exams"
    title = Column(String(200), nullable=False)
    type = Column(String(30), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("exam_templates.id"), nullable=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(String(20), default='draft')
    instructions = Column(Text)
    total_marks = Column(Integer, default=0)
    passing_marks = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    randomize_questions = Column(Boolean, default=False)
    browser_lock = Column(Boolean, default=False)
    force_fullscreen = Column(Boolean, default=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("exam_locations.id"), nullable=True)
    max_attempts = Column(Integer, default=1)
    tier = Column(String(10), nullable=True, default='Tier 1')
    scheduled_date = Column(Date, nullable=True)
    duration_mins = Column(Integer, nullable=True)

class ExamSection(EdVenturaBase):
    __tablename__ = "exam_sections"
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    title = Column(String(200))
    instructions = Column(Text)
    total_marks = Column(Integer, default=0)
    is_optional = Column(Boolean, default=False)
    order = Column(Integer, default=0)

class ExamSectionQuestion(EdVenturaBase):
    __tablename__ = "exam_section_questions"
    section_id = Column(UUID(as_uuid=True), ForeignKey("exam_sections.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("question_bank.id"), nullable=False)
    marks = Column(Integer, default=1)
    negative_marks = Column(Numeric(5,2), default=0)
    order = Column(Integer, default=0)

class StudentExamRegistration(EdVenturaBase):
    __tablename__ = "student_exam_registrations"
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    status = Column(String(20), default='registered')
    total_marks_obtained = Column(Numeric(10,2), nullable=True)
    started_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))

class StudentResponse(EdVenturaBase):
    __tablename__ = "student_responses"
    registration_id = Column(UUID(as_uuid=True), ForeignKey("student_exam_registrations.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("question_bank.id"), nullable=False)
    selected_answer = Column(Text)
    marks_obtained = Column(Numeric(10,2), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    evaluated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    remarks = Column(Text)


class StudentPerformanceAnalytics(EdVenturaBase):
    __tablename__ = "student_performance_analytics"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=True)
    total_marks = Column(Numeric(10,2))
    marks_obtained = Column(Numeric(10,2))
    percentage = Column(Numeric(5,2))
    percentile_class = Column(Numeric(5,2))
    percentile_section = Column(Numeric(5,2), nullable=True)
    swot_strengths = Column(JSON, default=[])
    swot_weaknesses = Column(JSON, default=[])
    swot_opportunities = Column(JSON, default=[])
    swot_threats = Column(JSON, default=[])
    topic_wise_breakdown = Column(JSON, default={})
    learning_velocity = Column(Numeric(10,2))
    consistency_score = Column(Numeric(5,2))

class ClassSectionAnalytics(EdVenturaBase):
    __tablename__ = "class_section_analytics"
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section = Column(String(20))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=True)
    average = Column(Numeric(10,2))
    median = Column(Numeric(10,2))
    highest = Column(Numeric(10,2))
    lowest = Column(Numeric(10,2))
    pass_percentage = Column(Numeric(5,2))
    topic_wise_average = Column(JSON, default={})
    teacher_id = Column(UUID(as_uuid=True), nullable=True)

class PDFReportLog(EdVenturaBase):
    __tablename__ = "pdf_report_logs"
    report_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    file_path = Column(String(500))
    report_metadata = Column(JSON, default={})

class XPEvent(EdVenturaBase):
    __tablename__ = "xp_events"
    user_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False)
    xp_awarded = Column(Integer, nullable=False)
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)

class SkillTreeProgress(EdVenturaBase):
    __tablename__ = "skill_tree_progress"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    skill_node = Column(String(100), nullable=False)
    progress = Column(Numeric(5,2), default=0)
    level = Column(Integer, default=1)
    unlocked_at = Column(DateTime(timezone=True))
    


class AdaptiveTestConfig(EdVenturaBase):
    __tablename__ = "adaptive_test_config"
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), unique=True, nullable=False)
    enabled = Column(Boolean, default=False)
    initial_difficulty = Column(String(20), default='medium')
    adaptive_rule = Column(JSON, default={})

class CompetitiveCohort(EdVenturaBase):
    __tablename__ = "competitive_cohorts"
    name = Column(String(100), nullable=False)
    exam_type = Column(String(50), nullable=False)
    total_participants = Column(Integer, default=0)
    score_distribution = Column(JSON, default={})

class ExamLocation(EdVenturaBase):
    __tablename__ = "exam_locations"
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, default=30)

class ExamInvigilator(EdVenturaBase):
    __tablename__ = "exam_invigilators"
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("exam_locations.id"), nullable=True)
    invigilator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

class ResultAccessCode(EdVenturaBase):
    __tablename__ = "result_access_codes"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    access_code = Column(String(12), unique=True, nullable=False)
    is_used = Column(Boolean, default=False)

class RevisionPlan(EdVenturaBase):
    __tablename__ = "revision_plans"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    plan_data = Column(JSON, default={})
    generated_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    expires_at = Column(DateTime(timezone=True))

class ExamBoardConfig(EdVenturaBase):
    __tablename__ = "exam_board_config"
    board_name = Column(String(50), nullable=False)
    subject_code = Column(String(20))
    max_marks = Column(Integer)
    passing_marks = Column(Integer)
    grading_system = Column(JSON, default='{}')

class ParentExamReport(EdVenturaBase):
    __tablename__ = "parent_exam_reports"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    summary_html = Column(Text)
    generated_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class ExternalAPIKey(EdVenturaBase):
    __tablename__ = "external_api_keys"
    provider = Column(String(50), nullable=False)
    api_key = Column(String(200), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)

class FeatureGate(EdVenturaBase):
    __tablename__ = "feature_gating"
    __table_args__ = (
        sa.UniqueConstraint('tenant_id', 'feature_name', name='uq_feature_gating_tenant_feature'),
    )
    feature_name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=False)