from uuid import UUID

from sqlalchemy import select

class VoiceService:
    def __init__(self, db):
        self.db = db
        self.tenant_id = None

    async def process_command(self, text: str, tenant_id: UUID, teacher_id: UUID) -> dict:
        self.tenant_id = tenant_id
        text = text.lower().strip()
        # Very basic intent parsing
        if "mark grade" in text and "present" in text:
            # extract class name from text
            words = text.split()
            grade_idx = words.index("grade")
            if grade_idx + 1 < len(words):
                class_name = words[grade_idx + 1]
                # find class by name
                from app.models.class_ import Class
                # search class (simplified)
                cls = await self.db.execute(select(Class).where(Class.name.ilike(f"%{class_name}%"), Class.tenant_id == self.tenant_id)).scalar_one_or_none()
                if not cls:
                    return {"error": "Class not found"}
                # mark all active students present
                from app.models.student import Student
                students = (await self.db.execute(select(Student).where(Student.class_id == cls.id, Student.is_active == True))).scalars().all()
                # call marking service (dependency injection omitted for brevity)
                return {"status": "queued", "students_count": len(students)}
        return {"error": "Could not understand command"}