from sqlalchemy import select


class SubstituteAllocationAI:
    async def suggest_substitute(self, absent_teacher_id, class_id, date, period, db, tenant_id):
        # Find teachers free in that period, weighted by subject match
        from app.models.attendance_models import TeacherClassAssignment
        from app.models.user import User
        # Get all teachers except absent one
        teachers = await db.execute(
            select(User).where(User.tenant_id == tenant_id, User.is_active == True, User.id != absent_teacher_id)
        )
        scores = []
        for teacher in teachers.scalars():
            # check workload
            assignments = await db.execute(
                select(TeacherClassAssignment).where(
                    TeacherClassAssignment.teacher_id == teacher.id,
                    TeacherClassAssignment.effective_from <= date,
                    TeacherClassAssignment.period_number == period
                )
            )
            if assignments.scalar_one_or_none():
                continue  # busy
            # score based on subject similarity (mock)
            score = 1.0
            scores.append({"teacher_id": teacher.id, "full_name": teacher.full_name, "score": score})
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:3]