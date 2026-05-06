from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_tenant
from app.core.permissions import PermissionChecker
from app.models.exam_models import AdaptiveTestConfig, ClassSectionAnalytics, ExamInvigilator, ExamLocation, SkillTreeProgress, StudentExamRegistration, StudentPerformanceAnalytics, StudentResponse
from app.models.student import Student
from app.models.user import User
from app.modules.exam.services.question_service import QuestionService
from app.modules.exam.services.exam_service import ExamService
from app.modules.exam.services.subject_service import SubjectService
from app.modules.exam import exam_schemas as schemas

from app.modules.exam.services.ai_question_generator import AIQuestionGenerator
from app.modules.exam.services.adaptive_testing import AdaptiveTestingService
from app.modules.exam.services.competitive_benchmarking import CompetitiveBenchmarkingService
from app.modules.exam.services.study_recommendations import StudyRecommendationService
from app.modules.exam.services.performance_alerts import PerformanceAlertService
from app.modules.exam.services.certificate_service import CertificateService
from app.modules.exam.services.result_publishing import ResultPublishingService
from app.modules.exam.services.analytics_service import AnalyticsService
from app.modules.exam.services.pdf_report_service import PDFReportService

from app.modules.exam.services.board_compliance import BoardComplianceService
from app.modules.exam.services.parent_report_service import ParentReportService
from app.modules.exam.services.feature_gating_service import FeatureGatingService
from app.modules.exam.services.external_api_service import ExternalAPIService

router = APIRouter(prefix="/exam", tags=["Exam & Assessment"])

async def get_question_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> QuestionService:
    return QuestionService(db, UUID(tenant_id))

async def get_exam_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ExamService:
    return ExamService(db, UUID(tenant_id))

async def get_subject_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> SubjectService:
    return SubjectService(db, UUID(tenant_id))

# Subjects
@router.post("/subjects", response_model=schemas.SubjectOut, dependencies=[Depends(PermissionChecker("subject:create"))])
async def create_subject(data: schemas.SubjectCreate, svc: SubjectService = Depends(get_subject_service)):
    return await svc.create_subject(data.dict())

@router.get("/subjects", response_model=List[schemas.SubjectOut], dependencies=[Depends(PermissionChecker("subject:read"))])
async def list_subjects(svc: SubjectService = Depends(get_subject_service)):
    return await svc.list_subjects()

@router.post("/subjects/{subject_id}/topics", response_model=schemas.TopicOut, dependencies=[Depends(PermissionChecker("subject:create"))])
async def create_topic(subject_id: UUID, data: schemas.TopicCreate, svc: SubjectService = Depends(get_subject_service)):
    data.subject_id = subject_id
    return await svc.create_topic(data.dict())

@router.get("/subjects/{subject_id}/topics", response_model=List[schemas.TopicOut], dependencies=[Depends(PermissionChecker("subject:read"))])
async def list_topics(subject_id: UUID, svc: SubjectService = Depends(get_subject_service)):
    return await svc.list_topics(subject_id)

# Questions
@router.post("/questions", response_model=schemas.QuestionOut, dependencies=[Depends(PermissionChecker("question:create"))])
async def create_question(data: schemas.QuestionCreate, current_user: User = Depends(get_current_user),
                          svc: QuestionService = Depends(get_question_service)):
    try:
        return await svc.create_question(data, current_user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.put("/questions/{question_id}", response_model=schemas.QuestionOut, dependencies=[Depends(PermissionChecker("question:update"))])
async def update_question(question_id: UUID, data: schemas.QuestionUpdate, svc: QuestionService = Depends(get_question_service)):
    try:
        return await svc.update_question(question_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.get("/questions/{question_id}", response_model=schemas.QuestionOut, dependencies=[Depends(PermissionChecker("question:read"))])
async def get_question(question_id: UUID, svc: QuestionService = Depends(get_question_service)):
    q = await svc.get_question(question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    return q

@router.get("/questions", response_model=List[schemas.QuestionOut], dependencies=[Depends(PermissionChecker("question:read"))])
async def list_questions(subject_id: Optional[UUID] = None, topic_id: Optional[UUID] = None,
                         difficulty: Optional[str] = None, question_type: Optional[str] = None,
                         skip: int = 0, limit: int = 100, svc: QuestionService = Depends(get_question_service)):
    return await svc.list_questions(subject_id, topic_id, difficulty, question_type, skip, limit)

@router.post("/questions/bulk-import", response_model=schemas.BulkImportResult, dependencies=[Depends(PermissionChecker("question:create"))])
async def bulk_import(file: UploadFile = File(...), file_type: str = Query(..., description="csv, xlsx, json"),
                      current_user: User = Depends(get_current_user), svc: QuestionService = Depends(get_question_service)):
    contents = await file.read()
    try:
        return await svc.bulk_import(contents, file_type, current_user.id)
    except Exception as e:
        raise HTTPException(400, str(e))

# Exam Templates (Blueprint)
@router.post("/templates", response_model=schemas.ExamTemplateOut, dependencies=[Depends(PermissionChecker("blueprint:create"))])
async def create_template(data: schemas.ExamTemplateCreate, current_user: User = Depends(get_current_user),
                          svc: ExamService = Depends(get_exam_service)):
    template = await svc.create_template(data, current_user.id)
    return template


# Exams
@router.post("/exams", response_model=schemas.ExamOut, dependencies=[Depends(PermissionChecker("exam:create"))])
async def create_exam(data: schemas.ExamCreate, sections: List[schemas.SectionCreate],
                     current_user: User = Depends(get_current_user), svc: ExamService = Depends(get_exam_service)):
    exam = await svc.create_exam(data, sections, current_user.id)
    # Build full output
    return exam

@router.put("/exams/{exam_id}/status", response_model=schemas.ExamOut, dependencies=[Depends(PermissionChecker("exam:update"))])
async def update_exam_status(exam_id: UUID, status: str = Query(..., description="draft/review/approved/published/archived"),
                             current_user: User = Depends(get_current_user), svc: ExamService = Depends(get_exam_service)):
    try:
        exam = await svc.update_exam_status(exam_id, status, current_user.id)
        return exam
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/exams/{exam_id}", response_model=schemas.ExamOut, dependencies=[Depends(PermissionChecker("exam:read"))])
async def get_exam(exam_id: UUID, svc: ExamService = Depends(get_exam_service)):
    exam, sections = await svc.get_exam_with_sections(exam_id)
    if not exam:
        raise HTTPException(404, "Exam not found")
    # Transform to output (simplified)
    return {**exam.__dict__, "sections": [s.__dict__ for s in sections]}

# Student Registration
@router.post("/exams/{exam_id}/register", dependencies=[Depends(PermissionChecker("exam:update"))])
async def register_students(exam_id: UUID, student_ids: List[UUID], svc: ExamService = Depends(get_exam_service)):
    await svc.register_students(exam_id, student_ids)
    return {"message": "Students registered"}

@router.post("/attempt/{reg_id}/answer", response_model=schemas.StudentResponseOut)
async def submit_answer(reg_id: UUID, qid: UUID, answer: str, svc: ExamService = Depends(get_exam_service)):
    resp = await svc.submit_answer(reg_id, qid, answer)
    return resp

@router.post("/attempt/{reg_id}/finish")
async def finish_exam(reg_id: UUID, svc: ExamService = Depends(get_exam_service)):
    reg = await svc.finish_exam(reg_id)
    return {"total_marks": float(reg.total_marks_obtained), "status": reg.status}

@router.post("/attempt/{reg_id}/evaluate/{response_id}",
             response_model=schemas.StudentResponseOut,
             dependencies=[Depends(PermissionChecker("exam:update"))])
async def evaluate_response(reg_id: UUID, response_id: UUID,
                            data: schemas.EvaluateResponseRequest,
                            current_user: User = Depends(get_current_user),
                            svc: ExamService = Depends(get_exam_service)):
    try:
        return await svc.evaluate_response(reg_id, response_id, data.marks, data.remarks, current_user.id)
    except ValueError as e:
        raise HTTPException(404, str(e))



from app.modules.exam.services.analytics_service import AnalyticsService
from app.modules.exam.services.pdf_report_service import PDFReportService

async def get_analytics_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AnalyticsService:
    return AnalyticsService(db, UUID(tenant_id))

async def get_pdf_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> PDFReportService:
    return PDFReportService(db, UUID(tenant_id))

# Analytics
@router.post("/analytics/compute/{reg_id}")
async def compute_analytics(reg_id: UUID, svc: AnalyticsService = Depends(get_analytics_service)):
    await svc.compute_student_performance(reg_id)
    return {"message": "Analytics computed"}

@router.get("/analytics/student/{student_id}")
async def get_student_analytics(student_id: UUID, subject_id: Optional[UUID] = None,
                                svc: AnalyticsService = Depends(get_analytics_service)):
    analytics = await svc.get_student_analytics(student_id, subject_id)
    return analytics

@router.get("/analytics/class/{class_id}")
async def get_class_analytics(class_id: UUID, subject_id: Optional[UUID] = None,
                              svc: AnalyticsService = Depends(get_analytics_service)):
    analytics = await svc.get_class_analytics(class_id, subject_id)
    return analytics

@router.post("/analytics/class/compute/{exam_id}")
async def compute_class_analytics(exam_id: UUID, svc: AnalyticsService = Depends(get_analytics_service)):
    await svc.compute_class_analytics(exam_id)
    return {"message": "Class analytics computed"}

# PDF Reports
@router.post("/reports/individual/{student_id}/{exam_id}")
async def individual_report(student_id: UUID, exam_id: UUID,
                            current_user: User = Depends(get_current_user),
                            svc: PDFReportService = Depends(get_pdf_service)):
    try:
        path = await svc.generate_individual_report(student_id, exam_id)
        return FileResponse(path, media_type="application/pdf",
                            filename=f"report_individual_{student_id}_{exam_id}.pdf")
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/reports/class/{class_id}/{exam_id}")
async def class_report(class_id: UUID, exam_id: UUID, current_user: User = Depends(get_current_user),
                       svc: PDFReportService = Depends(get_pdf_service)):
    try:
        path = await svc.generate_class_report(class_id, exam_id)
        return FileResponse(path, media_type="application/pdf",
                            filename=f"report_class_{class_id}_{exam_id}.pdf")
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/reports/institutional")
async def institutional_report(current_user: User = Depends(get_current_user),
                               svc: PDFReportService = Depends(get_pdf_service)):
    path = await svc.generate_institutional_report()
    return FileResponse(path, media_type="application/pdf",
                        filename="report_institutional.pdf")

# Gamification endpoints (directly in exam router to award XP after exam finish)
@router.post("/finish/{reg_id}/gamify")
async def finish_exam_with_gamification(reg_id: UUID, svc: ExamService = Depends(get_exam_service),
                                        analytics_svc: AnalyticsService = Depends(get_analytics_service)):
    # Finish exam and compute analytics + award XP
    reg = await svc.finish_exam(reg_id)   # already computes marks
    await analytics_svc.compute_student_performance(reg_id)
    return {"total_marks": float(reg.total_marks_obtained), "status": reg.status}


async def get_ai_question_gen(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AIQuestionGenerator:
    return AIQuestionGenerator(db, UUID(tenant_id))

async def get_adaptive_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> AdaptiveTestingService:
    return AdaptiveTestingService(db, UUID(tenant_id))

async def get_comp_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> CompetitiveBenchmarkingService:
    return CompetitiveBenchmarkingService(db, UUID(tenant_id))

async def get_study_rec_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> StudyRecommendationService:
    return StudyRecommendationService(db, UUID(tenant_id))

async def get_perf_alert_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> PerformanceAlertService:
    return PerformanceAlertService(db, UUID(tenant_id))

async def get_cert_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> CertificateService:
    return CertificateService(db, UUID(tenant_id))

async def get_result_pub_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ResultPublishingService:
    return ResultPublishingService(db, UUID(tenant_id))
    
# AI Question Generator
@router.post("/ai/generate-questions/{template_id}")
async def generate_questions(template_id: UUID, gen: AIQuestionGenerator = Depends(get_ai_question_gen)):
    questions = await gen.generate_questions(template_id)
    return {"questions": questions}

# Adaptive Testing
@router.post("/adaptive/config", response_model=schemas.AdaptiveConfigOut, dependencies=[Depends(PermissionChecker("exam:update"))])
async def set_adaptive_config(exam_id: UUID, config: schemas.AdaptiveConfigCreate,
                              db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    # Check if config already exists
    existing = (await db.execute(select(AdaptiveTestConfig).where(AdaptiveTestConfig.exam_id == exam_id, AdaptiveTestConfig.tenant_id == UUID(tenant_id)))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Adaptive config already exists for this exam")
    cfg = AdaptiveTestConfig(tenant_id=UUID(tenant_id), exam_id=exam_id, **config.dict())
    db.add(cfg)
    await db.commit()
    return cfg

@router.get("/adaptive/next-question")
async def adaptive_next_question(reg_id: UUID, exam_id: UUID, subject_id: UUID,
                                 topic_id: Optional[UUID] = None,
                                 adapt: AdaptiveTestingService = Depends(get_adaptive_service)):
    question = await adapt.select_question_for_student(reg_id, exam_id, subject_id, topic_id)
    if not question:
        raise HTTPException(404, "No suitable question")
    return question

# Competitive Benchmarking
@router.post("/competitive/cohort", response_model=schemas.CompetitiveCohortOut)
async def create_cohort(data: schemas.CompetitiveCohortCreate,
                        comp: CompetitiveBenchmarkingService = Depends(get_comp_service)):
    return await comp.upload_cohort(data.dict())

@router.get("/competitive/percentile")
async def get_percentile(student_id: UUID, exam_id: UUID, cohort_id: UUID,
                         comp: CompetitiveBenchmarkingService = Depends(get_comp_service)):
    try:
        return await comp.get_percentile(student_id, exam_id, cohort_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

# Study Recommendations
@router.get("/recommendations/{student_id}/{subject_id}", response_model=List[schemas.StudyRecommendation])
async def recommendations(student_id: UUID, subject_id: UUID,
                          svc: StudyRecommendationService = Depends(get_study_rec_service)):
    return await svc.generate_recommendations(student_id, subject_id)

@router.post("/revision-plan/{student_id}/{subject_id}", response_model=schemas.RevisionPlanOut)
async def create_revision_plan(student_id: UUID, subject_id: UUID, days: int = 7,
                               svc: StudyRecommendationService = Depends(get_study_rec_service)):
    try:
        plan = await svc.generate_revision_plan(student_id, subject_id, days)
        return plan
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/revision-plan/{student_id}/{subject_id}", response_model=schemas.RevisionPlanOut)
async def get_revision_plan(student_id: UUID, subject_id: UUID,
                            svc: StudyRecommendationService = Depends(get_study_rec_service)):
    plan = await svc.get_revision_plan(student_id, subject_id)
    if not plan:
        raise HTTPException(404, "No active revision plan")
    return plan

# Performance Alerts (manual trigger)
@router.post("/alerts/check/{student_id}")
async def check_alerts(student_id: UUID, subject_id: UUID,
                       alert_svc: PerformanceAlertService = Depends(get_perf_alert_service)):
    await alert_svc.check_and_alert(student_id, subject_id)
    return {"message": "Alerts processed"}

# Certificate & Transcript
@router.post("/certificate/{student_id}/{exam_id}")
async def generate_certificate(student_id: UUID, exam_id: UUID,
                               cert_svc: CertificateService = Depends(get_cert_service)):
    path = await cert_svc.generate_certificate(student_id, exam_id)
    return FileResponse(path, media_type="application/pdf",
                        filename=f"certificate_{student_id}_{exam_id}.pdf")

@router.post("/transcript/{student_id}")
async def generate_transcript(student_id: UUID,
                              cert_svc: CertificateService = Depends(get_cert_service)):
    path = await cert_svc.generate_transcript(student_id)
    return FileResponse(path, media_type="application/pdf",
                        filename=f"transcript_{student_id}.pdf")

# Result Publishing
@router.post("/publish/{student_id}/{exam_id}")
async def publish_result(student_id: UUID, exam_id: UUID,
                         pub_svc: ResultPublishingService = Depends(get_result_pub_service)):
    code = await pub_svc.publish_result(student_id, exam_id)
    return {"access_code": code}

@router.get("/results/{access_code}")
async def view_result(access_code: str,
                      pub_svc: ResultPublishingService = Depends(get_result_pub_service)):
    result = await pub_svc.get_result_by_code(access_code)
    if not result:
        raise HTTPException(404, "Invalid access code or no result published")
    return result


# Dependencies
async def get_board_compliance_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> BoardComplianceService:
    return BoardComplianceService(db, UUID(tenant_id))

async def get_parent_report_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ParentReportService:
    return ParentReportService(db, UUID(tenant_id))

async def get_feature_gating_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> FeatureGatingService:
    return FeatureGatingService(db, UUID(tenant_id))

async def get_external_api_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> ExternalAPIService:
    return ExternalAPIService(db, UUID(tenant_id))

# ================================================================
# Phase 4 Routes
# ================================================================

# Board Compliance
@router.post("/board-config", response_model=schemas.BoardConfigOut, dependencies=[Depends(PermissionChecker("exam:update"))])
async def create_board_config(data: schemas.BoardConfigCreate, svc: BoardComplianceService = Depends(get_board_compliance_service)):
    return await svc.create_board_config(data.dict())

@router.get("/board-config", response_model=List[schemas.BoardConfigOut], dependencies=[Depends(PermissionChecker("exam:read"))])
async def list_board_configs(svc: BoardComplianceService = Depends(get_board_compliance_service)):
    return await svc.list_board_configs()

@router.get("/board-config/{board_name}/grade")
async def get_grade(board_name: str, percentage: float, svc: BoardComplianceService = Depends(get_board_compliance_service)):
    grade = await svc.calculate_grade(board_name, percentage)
    return {"grade": grade}

# Parent Reports
@router.post("/reports/parent/{student_id}/{exam_id}", response_model=schemas.ParentReportOut)
async def generate_parent_report(student_id: UUID, exam_id: UUID, svc: ParentReportService = Depends(get_parent_report_service)):
    report = await svc.generate_parent_report(student_id, exam_id)
    return report

@router.get("/reports/parent/{student_id}/{exam_id}", response_model=schemas.ParentReportOut)
async def get_parent_report(student_id: UUID, exam_id: UUID, svc: ParentReportService = Depends(get_parent_report_service)):
    report = await svc.get_report(student_id, exam_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report

# Feature Gating
@router.get("/features", response_model=List[dict], dependencies=[Depends(PermissionChecker("system:read"))])
async def list_features(svc: FeatureGatingService = Depends(get_feature_gating_service)):
    features = await svc.get_all_features()
    return [{"feature_name": f.feature_name, "enabled": f.enabled} for f in features]

@router.post("/features", response_model=dict, dependencies=[Depends(PermissionChecker("system:write"))])
async def toggle_feature(data: schemas.FeatureGateUpdate, svc: FeatureGatingService = Depends(get_feature_gating_service)):
    gate = await svc.set_feature(data.feature_name, data.enabled)
    return {"feature_name": gate.feature_name, "enabled": gate.enabled}

# External API Keys
@router.post("/api-keys", response_model=schemas.ExternalAPIKeyOut, dependencies=[Depends(PermissionChecker("system:write"))])
async def register_api_key(data: schemas.ExternalAPIKeyCreate, svc: ExternalAPIService = Depends(get_external_api_service)):
    return await svc.register_api_key(data.provider, data.api_key)

@router.post("/api-keys/validate")
async def validate_api_key(provider: str, api_key: str, svc: ExternalAPIService = Depends(get_external_api_service)):
    valid = await svc.validate_api_key(provider, api_key)
    return {"valid": valid}

@router.get("/api-keys", response_model=List[schemas.ExternalAPIKeyOut], dependencies=[Depends(PermissionChecker("system:read"))])
async def list_api_keys(svc: ExternalAPIService = Depends(get_external_api_service)):
    return await svc.list_api_keys()


@router.post("/locations", response_model=schemas.ExamLocationOut, dependencies=[Depends(PermissionChecker("exam:create"))])
async def create_location(data: schemas.ExamLocationCreate, db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    loc = ExamLocation(tenant_id=UUID(tenant_id), **data.dict())
    db.add(loc)
    await db.commit()
    return loc

@router.get("/locations", response_model=List[schemas.ExamLocationOut], dependencies=[Depends(PermissionChecker("exam:read"))])
async def list_locations(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    stmt = select(ExamLocation).where(ExamLocation.tenant_id == UUID(tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/invigilators/assign", dependencies=[Depends(PermissionChecker("exam:update"))])
async def assign_invigilators(data: schemas.InvigilatorAssign, db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    for inv_id in data.invigilator_ids:
        assignment = ExamInvigilator(
            tenant_id=UUID(tenant_id),
            exam_id=data.exam_id,
            location_id=data.location_id,
            invigilator_id=inv_id
        )
        db.add(assignment)
    await db.commit()
    return {"message": f"{len(data.invigilator_ids)} invigilators assigned"}

@router.get("/invigilators/{exam_id}", response_model=List[dict], dependencies=[Depends(PermissionChecker("exam:read"))])
async def list_invigilators(exam_id: UUID, db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    stmt = select(ExamInvigilator).where(ExamInvigilator.exam_id == exam_id, ExamInvigilator.tenant_id == UUID(tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/analytics/teacher-effectiveness/{subject_id}", response_model=List[schemas.TeacherEffectivenessOut], dependencies=[Depends(PermissionChecker("exam:read"))])
async def teacher_effectiveness(subject_id: UUID, analytics_svc: AnalyticsService = Depends(get_analytics_service)):
    return await analytics_svc.get_teacher_effectiveness(subject_id)

@router.get("/alerts/toppers/{exam_id}", response_model=List[schemas.TopperOut], dependencies=[Depends(PermissionChecker("exam:read"))])
async def get_toppers(exam_id: UUID, alert_svc: PerformanceAlertService = Depends(get_perf_alert_service)):
    await alert_svc.check_toppers(exam_id)
    # Fetch the top 3 from DB
    toppers = (await alert_svc.db.execute(
        select(StudentPerformanceAnalytics.student_id, StudentPerformanceAnalytics.percentage, Student.first_name, Student.last_name)
        .join(Student, StudentPerformanceAnalytics.student_id == Student.id)
        .where(StudentPerformanceAnalytics.exam_id == exam_id, StudentPerformanceAnalytics.tenant_id == alert_svc.tenant_id)
        .order_by(StudentPerformanceAnalytics.percentage.desc()).limit(3)
    )).all()
    return [{"student_id": t.student_id, "student_name": f"{t.first_name} {t.last_name}", "percentage": float(t.percentage)} for t in toppers]

@router.get("/alerts/dropout-risk", response_model=List[schemas.DropoutRiskOut], dependencies=[Depends(PermissionChecker("exam:read"))])
async def dropout_risk(alert_svc: PerformanceAlertService = Depends(get_perf_alert_service)):
    risk = await alert_svc.check_dropout_risk()
    return risk


@router.post("/questions/export", response_class=Response)
async def export_questions(filters: schemas.BulkExportRequest,
                           svc: QuestionService = Depends(get_question_service)):
    content = await svc.export_questions(filters.dict(exclude_none=True), filters.file_format)
    media_type_map = {"json": "application/json", "csv": "text/csv", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    return Response(content=content, media_type=media_type_map[filters.file_format])


@router.get("/analytics/comparative/{student_id}/{exam_id}", response_model=schemas.ComparativeAnalyticsOut)
async def comparative_analytics(student_id: UUID, exam_id: UUID, analytics_svc: AnalyticsService = Depends(get_analytics_service)):
    perf = (await analytics_svc.db.execute(
        select(StudentPerformanceAnalytics).where(
            StudentPerformanceAnalytics.student_id == student_id,
            StudentPerformanceAnalytics.exam_id == exam_id,
            StudentPerformanceAnalytics.tenant_id == analytics_svc.tenant_id
        )
    )).scalar_one_or_none()
    if not perf:
        raise HTTPException(404, "Performance not found")
    class_an = (await analytics_svc.db.execute(
        select(ClassSectionAnalytics).where(
            ClassSectionAnalytics.class_id == perf.student.class_id,  # you'd need to fetch student's class
            ClassSectionAnalytics.exam_id == exam_id,
            ClassSectionAnalytics.tenant_id == analytics_svc.tenant_id
        )
    )).scalar_one_or_none()
    # simplified return
    return schemas.ComparativeAnalyticsOut(
        student_percentile=float(perf.percentile_class),
        class_average=float(class_an.average) if class_an else 0,
        section_average=0,  # if no section analytics
        school_average=None
    )
    
    
@router.get("/skill-tree/{student_id}/{subject_id}", response_model=List[schemas.SkillTreeProgressOut])
async def get_skill_tree(student_id: UUID, subject_id: UUID,
                         db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    stmt = select(SkillTreeProgress).where(
        SkillTreeProgress.student_id == student_id,
        SkillTreeProgress.subject_id == subject_id,
        SkillTreeProgress.tenant_id == UUID(tenant_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/eligibility/{student_id}/{exam_id}")
async def exam_eligibility(student_id: UUID, exam_id: UUID,
                           db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)):
    # Check attendance from attendance module
    from app.modules.attendance.services.integration_service import IntegrationService
    att_svc = IntegrationService(db, UUID(tenant_id))
    att_elig = await att_svc.check_exam_eligibility(student_id)  # returns {eligible, attendance_percent, min_required}
    # Check fee clearance
    from app.modules.finance.services.integration_service import FinanceIntegrationService
    fin_svc = FinanceIntegrationService(db, UUID(tenant_id))
    fee_clear = await fin_svc.check_fee_clearance(student_id)
    return {
        "attendance_eligible": att_elig["eligible"],
        "attendance_percent": att_elig["attendance_percent"],
        "fee_clear": fee_clear["clear"],
        "due_amount": fee_clear.get("due_amount", 0)
    }
    

# ---------- Manual Evaluation (teacher grades subjective/viva/etc.) ----------
from pydantic import BaseModel, Field

class ManualGradeRequest(BaseModel):
    question_id: UUID
    marks_awarded: float = Field(..., ge=0)
    remarks: Optional[str] = None

@router.put("/attempt/{reg_id}/evaluate", dependencies=[Depends(PermissionChecker("exam:evaluate"))])
async def manual_evaluate(
    reg_id: UUID,
    grades: List[ManualGradeRequest],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant)
):
    # Fetch registration
    reg = await db.get(StudentExamRegistration, reg_id)
    if not reg or str(reg.tenant_id) != tenant_id:
        raise HTTPException(404, "Registration not found")
    if reg.status not in ("submitted", "graded"):
        raise HTTPException(400, "Exam must be submitted before grading")

    total_obtained = 0
    for g in grades:
        resp = (await db.execute(
            select(StudentResponse).where(
                StudentResponse.registration_id == reg_id,
                StudentResponse.question_id == g.question_id,
                StudentResponse.tenant_id == UUID(tenant_id)
            )
        )).scalar_one_or_none()
        if not resp:
            raise HTTPException(404, f"Response not found for question {g.question_id}")

        resp.marks_obtained = g.marks_awarded
        resp.remarks = g.remarks
        resp.evaluated_by = current_user.id
        resp.is_correct = None           # manual grading, not auto‑correct
        db.add(resp)
        total_obtained += g.marks_awarded

    # Recalculate total for registration
    reg.total_marks_obtained = total_obtained
    reg.status = "graded"
    await db.commit()

    return {"registration_id": reg_id, "total_marks": total_obtained}