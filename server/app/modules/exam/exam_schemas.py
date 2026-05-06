from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

# Subject & Topic
class SubjectCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None

class SubjectOut(BaseModel):
    id: UUID
    name: str
    code: Optional[str]
    description: Optional[str]
    is_active: bool
    class Config: from_attributes = True

class TopicCreate(BaseModel):
    subject_id: UUID
    name: str
    description: Optional[str] = None

class TopicOut(BaseModel):
    id: UUID
    subject_id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    class Config: from_attributes = True

# Question
class OptionItem(BaseModel):
    option: str   # A,B,C,D
    text: str

class QuestionCreate(BaseModel):
    subject_id: UUID
    topic_id: Optional[UUID] = None
    question_type: str = Field(..., pattern="^(mcq|subjective|true_false|fill_blank)$")
    difficulty: str = Field(..., pattern="^(easy|medium|hard|competitive)$")
    question_text: str
    options: Optional[List[OptionItem]] = None
    correct_answer: Optional[str] = None   # for mcq: "A", for others text
    marks: int = 1
    negative_marks: float = 0.0
    bloom_level: Optional[str] = None
    tags: Optional[List[str]] = []

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    options: Optional[List[OptionItem]] = None
    correct_answer: Optional[str] = None
    marks: Optional[int] = None
    negative_marks: Optional[float] = None
    difficulty: Optional[str] = None
    bloom_level: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class QuestionOut(BaseModel):
    id: UUID
    subject_id: UUID
    topic_id: Optional[UUID]
    question_type: str
    difficulty: str
    question_text: str
    options: Optional[List[OptionItem]]
    correct_answer: Optional[str]
    marks: int
    negative_marks: float
    bloom_level: Optional[str]
    tags: Optional[List[str]]
    version: int
    is_active: bool
    created_by: UUID
    class Config: from_attributes = True

# Exam Template (Blueprint)
class BlueprintSection(BaseModel):
    topic_id: Optional[UUID] = None
    weightage: float  # percentage of total marks
    difficulty_distribution: dict = {}  # e.g. {"easy":30,"medium":50,"hard":20}
    question_count: int
    marks_per_question: int

class ExamTemplateCreate(BaseModel):
    name: str
    subject_id: UUID
    blueprint: List[BlueprintSection]
    duration_minutes: Optional[int] = None

class ExamTemplateOut(BaseModel):
    id: UUID
    name: str
    subject_id: UUID
    blueprint: List[BlueprintSection]
    duration_minutes: Optional[int]
    is_active: bool
    created_by: UUID
    class Config: from_attributes = True

# Exam
class ExamCreate(BaseModel):
    title: str
    type: str
    subject_id: UUID
    class_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    instructions: Optional[str] = None
    total_marks: Optional[int] = None
    passing_marks: Optional[int] = None
    tier: Optional[str] = Field("Tier 1", pattern="^(Tier 1|Tier 2|Tier 3)$")
    scheduled_date: Optional[date] = None
    duration_mins: Optional[int] = None

class SectionCreate(BaseModel):
    title: Optional[str] = None
    instructions: Optional[str] = None
    total_marks: int = 0
    is_optional: bool = False
    questions: List[UUID] = []  # question ids

class ExamOut(BaseModel):
    id: UUID
    title: str
    type: str
    subject_id: UUID
    class_id: Optional[UUID]
    template_id: Optional[UUID]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: str
    instructions: Optional[str]
    total_marks: int
    passing_marks: int
    created_by: UUID
    approved_by: Optional[UUID]
    sections: List[dict] = []   # will include section details with questions
    class Config: from_attributes = True
    tier: Optional[str]
    scheduled_date: Optional[date]
    duration_mins: Optional[int]

# Bulk Import
class BulkImportResult(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    errors: List[str] = []

# Student exam registration
class StudentExamRegistrationCreate(BaseModel):
    exam_id: UUID
    student_ids: List[UUID]

class StudentResponseCreate(BaseModel):
    registration_id: UUID
    question_id: UUID
    selected_answer: str

class StudentResponseOut(BaseModel):
    id: UUID
    question_id: UUID
    selected_answer: Optional[str]
    marks_obtained: Optional[float]
    is_correct: Optional[bool]
    remarks: Optional[str] = None
    evaluated_by: Optional[UUID] = None
    class Config: from_attributes = True

class EvaluateResponseRequest(BaseModel):
    marks: float = Field(..., ge=0)
    remarks: Optional[str] = None

class StudentExamResultOut(BaseModel):
    registration_id: UUID
    student_id: UUID
    total_marks: float
    status: str
    responses: List[StudentResponseOut] = []
    
# SWOT
class SWOTOut(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

# Analytics
class StudentPerformanceAnalyticsOut(BaseModel):
    student_id: UUID
    subject_id: UUID
    exam_id: Optional[UUID]
    percentage: Optional[float]
    percentile_class: Optional[float]
    percentile_section: Optional[float]
    swot: SWOTOut
    topic_breakdown: dict
    learning_velocity: Optional[float]
    consistency_score: Optional[float]
    class Config: from_attributes = True

class ClassSectionAnalyticsOut(BaseModel):
    class_id: UUID
    section: Optional[str]
    subject_id: UUID
    exam_id: Optional[UUID]
    average: float
    median: float
    highest: float
    lowest: float
    pass_percentage: float
    topic_wise_average: dict
    class Config: from_attributes = True

class ComparativeAnalyticsOut(BaseModel):
    student_percentile: float
    class_average: float
    section_average: float
    school_average: Optional[float] = None

# PDF Reports
class ReportTypes:
    INDIVIDUAL = "individual"
    CLASS = "class"
    INSTITUTIONAL = "institutional"

class PDFReportOut(BaseModel):
    id: UUID
    report_type: str
    file_path: str
    generated_at: datetime

class PDFGenerationRequest(BaseModel):
    report_type: str = Field(..., pattern="^(individual|class|institutional)$")

# Gamification
class XPEventOut(BaseModel):
    user_id: UUID
    event_type: str
    xp_awarded: int
    created_at: datetime
    class Config: from_attributes = True

class SkillTreeProgressOut(BaseModel):
    student_id: UUID
    subject_id: UUID
    skill_node: str
    progress: float
    level: int
    class Config: from_attributes = True

# Additional Assessment Types (extend ExamCreate to support new types)
class ExamCreateExtended(ExamCreate):   # we can just add validation or keep separate
    type: str = Field(..., pattern="^(mcq|subjective|practical|viva|assignment|coding|oral|internal)$")
    
    
class AdaptiveConfigCreate(BaseModel):
    enabled: bool = False
    initial_difficulty: str = "medium"
    adaptive_rule: dict = {}

class AdaptiveConfigOut(BaseModel):
    id: UUID
    exam_id: UUID
    enabled: bool
    initial_difficulty: str
    adaptive_rule: dict
    class Config: from_attributes = True

class CompetitiveCohortCreate(BaseModel):
    name: str
    exam_type: str
    score_distribution: dict = {}  # percentile mapping

class CompetitiveCohortOut(BaseModel):
    id: UUID
    name: str
    exam_type: str
    total_participants: int
    score_distribution: dict

class ExamLocationCreate(BaseModel):
    name: str
    capacity: int = 30

class ExamLocationOut(BaseModel):
    id: UUID
    name: str
    capacity: int
    class Config: from_attributes = True

class ExamInvigilatorAssign(BaseModel):
    exam_id: UUID
    location_id: Optional[UUID] = None
    invigilator_ids: List[UUID]

class ResultAccessCodeOut(BaseModel):
    access_code: str
    student_id: UUID
    exam_id: UUID

class RevisionPlanOut(BaseModel):
    id: UUID
    student_id: UUID
    subject_id: UUID
    plan_data: dict
    generated_at: datetime
    expires_at: Optional[datetime]

class StudyRecommendation(BaseModel):
    topic_id: UUID
    topic_name: str
    current_score: float
    recommended_actions: List[str]   # e.g., "watch video", "solve 10 questions"
    resources: List[str]             # URLs or resource IDs
    
    

class BoardConfigCreate(BaseModel):
    board_name: str
    subject_code: Optional[str] = None
    max_marks: Optional[int] = None
    passing_marks: Optional[int] = None
    grading_system: dict = {}

class BoardConfigOut(BaseModel):
    id: UUID
    board_name: str
    subject_code: Optional[str]
    max_marks: Optional[int]
    passing_marks: Optional[int]
    grading_system: dict

class ParentReportOut(BaseModel):
    id: UUID
    student_id: UUID
    exam_id: UUID
    summary_html: str
    generated_at: datetime

class ExternalAPIKeyCreate(BaseModel):
    provider: str
    api_key: str

class ExternalAPIKeyOut(BaseModel):
    id: UUID
    provider: str
    is_active: bool

class FeatureGateUpdate(BaseModel):
    feature_name: str
    enabled: bool

class InvigilatorAssign(BaseModel):
    exam_id: UUID
    location_id: UUID
    invigilator_ids: List[UUID]

class TeacherEffectivenessOut(BaseModel):
    teacher_id: UUID
    subject_id: UUID
    average_performance: float
    total_students: int

class TopperOut(BaseModel):
    student_id: UUID
    student_name: str
    percentage: float

class DropoutRiskOut(BaseModel):
    student_id: UUID
    risk_level: str   # low, medium, high
    consecutive_drops: int

class BulkExportRequest(BaseModel):
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    file_format: str = "json"   # json, csv, xlsx