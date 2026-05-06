from uuid import UUID
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.exam_models import Exam, ExamSection, ExamSectionQuestion, ExamTemplate, Question, StudentExamRegistration, StudentResponse
from app.modules.exam import exam_schemas as schemas

class ExamService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ---------- Lifecycle ----------
    async def create_exam(self, data: schemas.ExamCreate, sections: list[schemas.SectionCreate], created_by: UUID) -> Exam:
        exam = Exam(
            tenant_id=self.tenant_id,
            title=data.title,
            type=data.type,
            subject_id=data.subject_id,
            class_id=data.class_id,
            template_id=data.template_id,
            start_time=data.start_time,
            end_time=data.end_time,
            instructions=data.instructions,
            total_marks=data.total_marks or 0,
            passing_marks=data.passing_marks or 0,
            status='draft',
            created_by=created_by
        )
        self.db.add(exam)
        await self.db.flush()

        for sec_data in sections:
            section = ExamSection(
                tenant_id=self.tenant_id,
                exam_id=exam.id,
                title=sec_data.title,
                instructions=sec_data.instructions,
                total_marks=sec_data.total_marks,
                is_optional=sec_data.is_optional,
                order=sec_data.order if hasattr(sec_data, 'order') else 0
            )
            self.db.add(section)
            await self.db.flush()
            for qid in sec_data.questions:
                link = ExamSectionQuestion(
                    tenant_id=self.tenant_id,
                    section_id=section.id,
                    question_id=qid,
                    # inherit marks from question? We'll fetch default from question.
                    marks=0,  # will update later
                    order=0
                )
                self.db.add(link)
        await self.db.commit()
        return exam

    async def update_exam_status(self, exam_id: UUID, status: str, user_id: UUID):
        exam = await self.db.get(Exam, exam_id)
        if not exam or exam.tenant_id != self.tenant_id:
            raise ValueError("Exam not found")
        exam.status = status
        if status == 'approved':
            exam.approved_by = user_id
        await self.db.commit()
        return exam

    async def get_exam_with_sections(self, exam_id: UUID):
        exam = await self.db.get(Exam, exam_id)
        if not exam or exam.tenant_id != self.tenant_id:
            return None
        sections_res = await self.db.execute(
            select(ExamSection).where(ExamSection.exam_id == exam_id).order_by(ExamSection.order)
        )
        sections = sections_res.scalars().all()
        return exam, sections

    # ---------- Student Registration & Attempts ----------
    async def register_students(self, exam_id: UUID, student_ids: list[UUID]):
        exam = await self.db.get(Exam, exam_id)
        if not exam or exam.tenant_id != self.tenant_id:
            raise ValueError("Exam not found")

        for sid in student_ids:
            # Count existing attempts for this student + exam
            existing_count = (await self.db.execute(
                select(func.count(StudentExamRegistration.id)).where(
                    StudentExamRegistration.exam_id == exam_id,
                    StudentExamRegistration.student_id == sid,
                    StudentExamRegistration.tenant_id == self.tenant_id
                )
            )).scalar() or 0

            if existing_count >= exam.max_attempts:
                raise HTTPException(400, f"Student {sid} has exhausted maximum attempts ({exam.max_attempts})")

            reg = StudentExamRegistration(
                tenant_id=self.tenant_id,
                exam_id=exam_id,
                student_id=sid,
                status='registered'
            )
            self.db.add(reg)
        await self.db.commit()

    async def submit_answer(self, reg_id: UUID, question_id: UUID, selected_answer: str):
        # auto-grade MCQ if possible
        reg = await self.db.get(StudentExamRegistration, reg_id)
        if not reg or reg.tenant_id != self.tenant_id:
            raise ValueError("Registration not found")
        question = await self.db.get(Question, question_id)
        if not question:
            raise ValueError("Question not found")
        is_correct = None
        marks = 0
        if question.question_type == 'mcq':
            if question.correct_answer and selected_answer.strip().upper() == question.correct_answer.strip().upper():
                is_correct = True
                marks = question.marks
            else:
                is_correct = False
                marks = -question.negative_marks if question.negative_marks else 0
        # For other types, manual evaluation later
        resp = StudentResponse(
            tenant_id=self.tenant_id,
            registration_id=reg_id,
            question_id=question_id,
            selected_answer=selected_answer,
            marks_obtained=marks,
            is_correct=is_correct
        )
        self.db.add(resp)
        await self.db.commit()
        return resp

    async def finish_exam(self, reg_id: UUID):
        reg = await self.db.get(StudentExamRegistration, reg_id)
        if not reg or reg.tenant_id != self.tenant_id:
            raise ValueError("Registration not found")
        reg.status = 'submitted'
        reg.submitted_at = datetime.utcnow()
        # Calculate total
        total = await self.db.execute(
            select(func.sum(StudentResponse.marks_obtained)).where(StudentResponse.registration_id == reg_id)
        )
        reg.total_marks_obtained = total.scalar() or 0
        await self.db.commit()
        return reg

    async def evaluate_response(self, reg_id: UUID, response_id: UUID,
                                marks: float, remarks: str | None, evaluated_by: UUID) -> StudentResponse:
        reg = await self.db.get(StudentExamRegistration, reg_id)
        if not reg or reg.tenant_id != self.tenant_id:
            raise ValueError("Registration not found")
        resp = await self.db.get(StudentResponse, response_id)
        if not resp or resp.registration_id != reg_id:
            raise ValueError("Response not found")
        resp.marks_obtained = marks
        resp.remarks = remarks
        resp.evaluated_by = evaluated_by
        if reg.status == 'submitted':
            total = await self.db.execute(
                select(func.sum(StudentResponse.marks_obtained)).where(
                    StudentResponse.registration_id == reg_id
                )
            )
            reg.total_marks_obtained = total.scalar() or 0
        await self.db.commit()
        return resp

    # ---------- Blueprint Builder ----------
    async def build_exam_from_blueprint(self, template_id: UUID, sections: list[schemas.SectionCreate] = None):
        template = await self.db.get(ExamTemplate, template_id)
        if not template or template.tenant_id != self.tenant_id:
            raise ValueError("Template not found")
        blueprint = template.blueprint  # list of BlueprintSection dicts
        # Auto-select questions based on blueprint criteria: topic, difficulty distribution, question count
        selected_questions = []
        for section_bp in blueprint:
            topic_id = section_bp.get('topic_id')
            question_count = section_bp['question_count']
            difficulty_dist = section_bp['difficulty_distribution']
            # For each difficulty level, fetch available questions meeting criteria
            for diff, percent in difficulty_dist.items():
                needed = int(question_count * percent / 100)
                if needed > 0:
                    stmt = select(Question).where(
                        Question.tenant_id == self.tenant_id,
                        Question.topic_id == topic_id,
                        Question.difficulty == diff,
                        Question.is_active == True
                    ).limit(needed)
                    result = await self.db.execute(stmt)
                    questions = result.scalars().all()
                    selected_questions.extend(questions)
            # Fallback if not enough: ignore difficulty
            if len(selected_questions) < question_count:
                remaining = question_count - len(selected_questions)
                stmt = select(Question).where(
                    Question.tenant_id == self.tenant_id,
                    Question.topic_id == topic_id,
                    Question.is_active == True
                ).limit(remaining)
                result = await self.db.execute(stmt)
                extra = result.scalars().all()
                selected_questions.extend(extra)
        # Return list of question IDs (with marks from blueprint)
        return [{"question_id": q.id, "marks": 3} for q in selected_questions]
    
    
    async def create_template(self, data: schemas.ExamTemplateCreate, created_by: UUID):
        template = ExamTemplate(
            tenant_id=self.tenant_id,
            name=data.name,
            subject_id=data.subject_id,
            blueprint=[s.dict() for s in data.blueprint],
            duration_minutes=data.duration_minutes,
            created_by=created_by
        )
        self.db.add(template)
        await self.db.commit()
        return template
