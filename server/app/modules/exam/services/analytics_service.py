from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from app.models.exam_models import (
    StudentResponse, StudentExamRegistration, Exam, ExamSectionQuestion,
    Question, StudentPerformanceAnalytics, ClassSectionAnalytics
)
from app.models.student import Student
from app.models.class_ import Class
import numpy as np

class AnalyticsService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def compute_student_performance(self, registration_id: UUID):
        """Compute analytics after an exam is submitted."""
        reg = await self.db.get(StudentExamRegistration, registration_id)
        if not reg or reg.tenant_id != self.tenant_id:
            return None
        exam = await self.db.get(Exam, reg.exam_id)
        if not exam:
            return None
        subject_id = exam.subject_id
        student_id = reg.student_id

        # Fetch all responses for this registration
        responses = (await self.db.execute(
            select(StudentResponse).where(StudentResponse.registration_id == registration_id)
        )).scalars().all()

        total_marks = exam.total_marks
        marks_obtained = sum(float(r.marks_obtained) for r in responses if r.marks_obtained)
        percentage = (marks_obtained / total_marks * 100) if total_marks else 0

        # Percentile calculation (within class and section)
        student = await self.db.get(Student, student_id)
        if not student:
            return None
        class_id = student.class_id
        section = student.section

        # All registrations for same exam (to compute percentile)
        all_regs = (await self.db.execute(
            select(StudentExamRegistration.total_marks_obtained).where(
                StudentExamRegistration.exam_id == exam.id,
                StudentExamRegistration.status == 'submitted',
                StudentExamRegistration.tenant_id == self.tenant_id
            )
        )).scalars().all()
        all_scores = sorted([float(m) for m in all_regs if m is not None])
        if all_scores:
            class_percentile = (sum(1 for s in all_scores if s < marks_obtained) / len(all_scores)) * 100
        else:
            class_percentile = 0

        section_regs = (await self.db.execute(
            select(StudentExamRegistration.total_marks_obtained)
            .where(
                StudentExamRegistration.exam_id == exam.id,
                StudentExamRegistration.status == 'submitted',
                StudentExamRegistration.tenant_id == self.tenant_id
            )
            .join(Student, StudentExamRegistration.student_id == Student.id)
            .where(Student.section == section)
        )).scalars().all()
        section_scores = sorted([float(m) for m in section_regs if m is not None])
        section_percentile = (sum(1 for s in section_scores if s < marks_obtained) / len(section_scores)) * 100 if section_scores else 0
        
        
        # # Section percentile (filter by section)
        # section_regs = (await self.db.execute(
        #     select(StudentExamRegistration.total_marks_obtained).where(
        #         StudentExamRegistration.exam_id == exam.id,
        #         StudentExamRegistration.status == 'submitted',
        #         StudentExamRegistration.tenant_id == self.tenant_id,
        #         # join with students to filter by section -> simpler: fetch all and filter in Python
        #     )
        # )).scalars().all()
        # For simplicity, we'll just compute class percentile; section percentile would need additional join.

        # Topic-wise breakdown
        topic_breakdown = {}
        for resp in responses:
            q = await self.db.get(Question, resp.question_id)
            if q and q.topic_id:
                tid = str(q.topic_id)
                if tid not in topic_breakdown:
                    topic_breakdown[tid] = {"total":0, "obtained":0}
                topic_breakdown[tid]["total"] += q.marks
                topic_breakdown[tid]["obtained"] += float(resp.marks_obtained) if resp.marks_obtained else 0

        # SWOT analysis
        swot = await self._compute_swot(topic_breakdown)

        # Learning velocity (comparison with previous exams same subject)
        previous = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.student_id == student_id,
                StudentPerformanceAnalytics.subject_id == subject_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            ).order_by(StudentPerformanceAnalytics.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        velocity = 0
        if previous and previous.percentage:
            velocity = percentage - float(previous.percentage)

        # Consistency score (standard deviation of marks across subjects? simplified)
        # We'll use a placeholder calculation: variance of topic percentages
        topic_percents = [v['obtained']/v['total']*100 for v in topic_breakdown.values() if v['total']>0]
        consistency = 100 - np.std(topic_percents) if topic_percents else 100

        # Upsert student_performance_analytics
        analytics = StudentPerformanceAnalytics(
            tenant_id=self.tenant_id,
            student_id=student_id,
            subject_id=subject_id,
            exam_id=exam.id,
            total_marks=total_marks,
            marks_obtained=marks_obtained,
            percentage=percentage,
            percentile_class=class_percentile,
            percentile_section=section_percentile,
            swot_strengths=swot['strengths'],
            swot_weaknesses=swot['weaknesses'],
            swot_opportunities=swot['opportunities'],
            swot_threats=swot['threats'],
            topic_wise_breakdown=topic_breakdown,
            learning_velocity=velocity,
            consistency_score=consistency
        )
        self.db.add(analytics)
        await self.db.commit()

        # Trigger gamification XP
        from app.modules.gamification.gamification_service import GamificationService
        gam = GamificationService(self.db, self.tenant_id)
        # Award XP for attempting exam
        await gam.award_xp(student_id, 'exam_attempt', 50, related_entity_id=exam.id)
        if percentage >= exam.passing_marks:
            await gam.award_xp(student_id, 'exam_pass', 100, related_entity_id=exam.id)
        if percentage >= 90:
            await gam.award_badge(student_id, 'student', 'top_performer')

        return analytics

    async def _compute_swot(self, topic_breakdown):
        strengths = []
        weaknesses = []
        opportunities = []
        threats = []
        for tid, data in topic_breakdown.items():
            if data['total'] == 0:
                continue
            pct = data['obtained'] / data['total'] * 100
            if pct >= 80:
                strengths.append(tid)
            elif pct < 50:
                weaknesses.append(tid)
            # Opportunities: topics with potential improvement (moderate scores)
            if 50 <= pct < 70:
                opportunities.append(tid)
            # Threats: consistently declining? We'll just flag topics with low performance and high weightage
            if pct < 40:
                threats.append(tid)
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats
        }

    async def get_student_analytics(self, student_id: UUID, subject_id: Optional[UUID] = None):
        stmt = select(StudentPerformanceAnalytics).where(
            StudentPerformanceAnalytics.student_id == student_id,
            StudentPerformanceAnalytics.tenant_id == self.tenant_id
        )
        if subject_id:
            stmt = stmt.where(StudentPerformanceAnalytics.subject_id == subject_id)
        res = await self.db.execute(stmt.order_by(StudentPerformanceAnalytics.created_at.desc()).limit(10))
        return res.scalars().all()

    async def compute_class_analytics(self, exam_id: UUID):
        exam = await self.db.get(Exam, exam_id)
        if not exam:
            return
        class_id = exam.class_id
        
        # Aggregate all student analytics for this exam
        analytics_list = (await self.db.execute(
            select(StudentPerformanceAnalytics).where(
                StudentPerformanceAnalytics.exam_id == exam_id,
                StudentPerformanceAnalytics.tenant_id == self.tenant_id
            )
        )).scalars().all()
        if not analytics_list:
            return
        scores = [float(a.percentage) for a in analytics_list if a.percentage]
        avg = np.mean(scores)
        med = np.median(scores)
        high = max(scores)
        low = min(scores)
        pass_count = sum(1 for s in scores if s >= exam.passing_marks)
        pass_pct = (pass_count / len(scores) * 100) if scores else 0

        # Topic-wise average
        topic_avg = {}
        for a in analytics_list:
            if a.topic_wise_breakdown:
                for tid, data in a.topic_wise_breakdown.items():
                    if tid not in topic_avg:
                        topic_avg[tid] = {"total":0, "obtained":0, "count":0}
                    topic_avg[tid]["total"] += data['total']
                    topic_avg[tid]["obtained"] += data['obtained']
                    topic_avg[tid]["count"] += 1
        for tid, vals in topic_avg.items():
            if vals['count'] > 0 and vals['total'] > 0:
                vals['average_percent'] = (vals['obtained'] / vals['total'] * 100)

        
        from app.models.attendance_models import TeacherClassAssignment
        teacher_assign = (await self.db.execute(
            select(TeacherClassAssignment.teacher_id)
            .where(
                TeacherClassAssignment.class_id == class_id,
                TeacherClassAssignment.subject_id == exam.subject_id,
                TeacherClassAssignment.is_deleted == False
            ).limit(1)
        )).scalar_one_or_none()
        teacher_id = teacher_assign.teacher_id if teacher_assign else None

        class_analytics = ClassSectionAnalytics(
            tenant_id=self.tenant_id,
            class_id=class_id,
            section=None,
            subject_id=exam.subject_id,
            exam_id=exam_id,
            average=avg,
            median=med,
            highest=high,
            lowest=low,
            teacher_id=teacher_id,
            pass_percentage=pass_pct,
            topic_wise_average=topic_avg
        )
        self.db.add(class_analytics)
        await self.db.commit()
        return class_analytics

    async def get_class_analytics(self, class_id: UUID, subject_id: Optional[UUID] = None):
        stmt = select(ClassSectionAnalytics).where(
            ClassSectionAnalytics.class_id == class_id,
            ClassSectionAnalytics.tenant_id == self.tenant_id
        )
        if subject_id:
            stmt = stmt.where(ClassSectionAnalytics.subject_id == subject_id)
        res = await self.db.execute(stmt.order_by(ClassSectionAnalytics.created_at.desc()).limit(10))
        return res.scalars().all()
    
    async def get_teacher_effectiveness(self, subject_id: UUID) -> list:
        """Return average performance per teacher for a subject."""
        from app.models.attendance_models import TeacherClassAssignment
        stmt = select(
            ClassSectionAnalytics.teacher_id,
            func.avg(ClassSectionAnalytics.average).label('avg_perf'),
            func.count(ClassSectionAnalytics.id).label('total')
        ).where(
            ClassSectionAnalytics.subject_id == subject_id,
            ClassSectionAnalytics.tenant_id == self.tenant_id,
            ClassSectionAnalytics.teacher_id != None
        ).group_by(ClassSectionAnalytics.teacher_id)
        rows = (await self.db.execute(stmt)).all()
        result = []
        for row in rows:
            result.append({
                "teacher_id": row.teacher_id,
                "subject_id": subject_id,
                "average_performance": float(row.avg_perf),
                "total_students": row.total
            })
        return result