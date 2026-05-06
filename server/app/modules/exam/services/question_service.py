from uuid import UUID
from pydantic import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.exam_models import Question, Subject, Topic
from app.modules.exam import exam_schemas as schemas
import hashlib
import pandas as pd
from io import BytesIO

class QuestionService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_question(self, data: schemas.QuestionCreate, created_by: UUID) -> Question:
        content = data.question_text
        if data.options:
            content += str(data.options)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        # Check existing
        existing = await self.db.execute(
            select(Question).where(Question.tenant_id == self.tenant_id, Question.content_hash == content_hash)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Duplicate question detected")
        question = Question(
            tenant_id=self.tenant_id,
            subject_id=data.subject_id,
            topic_id=data.topic_id,
            question_type=data.question_type,
            difficulty=data.difficulty,
            question_text=data.question_text,
            options=[o.dict() for o in data.options] if data.options else None,
            correct_answer=data.correct_answer,
            marks=data.marks,
            negative_marks=data.negative_marks,
            bloom_level=data.bloom_level,
            tags=data.tags or [],
            content_hash=content_hash,
            created_by=created_by
        )
        self.db.add(question)
        await self.db.commit()
        return question

    async def update_question(self, question_id: UUID, data: schemas.QuestionUpdate) -> Question:
        q = await self.db.get(Question, question_id)
        if not q or q.tenant_id != self.tenant_id:
            raise ValueError("Question not found")
        update_data = data.dict(exclude_unset=True)
        if 'options' in update_data and update_data['options'] is not None:
            update_data['options'] = [o.dict() if isinstance(o, schemas.OptionItem) else o for o in update_data['options']]
        for k, v in update_data.items():
            setattr(q, k, v)
        # Re-compute hash if content changed
        if 'question_text' in update_data or 'options' in update_data:
            content = q.question_text
            if q.options:
                content += str(q.options)
            q.content_hash = hashlib.sha256(content.encode()).hexdigest()
        await self.db.commit()
        return q

    async def get_question(self, question_id: UUID) -> Question:
        q = await self.db.get(Question, question_id)
        if not q or q.tenant_id != self.tenant_id:
            return None
        return q

    async def list_questions(self, subject_id: UUID = None, topic_id: UUID = None,
                             difficulty: str = None, question_type: str = None,
                             skip: int = 0, limit: int = 100) -> list:
        stmt = select(Question).where(Question.tenant_id == self.tenant_id, Question.is_deleted == False)
        if subject_id:
            stmt = stmt.where(Question.subject_id == subject_id)
        if topic_id:
            stmt = stmt.where(Question.topic_id == topic_id)
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)
        if question_type:
            stmt = stmt.where(Question.question_type == question_type)
        stmt = stmt.order_by(Question.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def bulk_import(self, file_bytes: bytes, file_type: str, created_by: UUID) -> schemas.BulkImportResult:
        if file_type == 'csv':
            df = pd.read_csv(BytesIO(file_bytes))
        elif file_type == 'xlsx':
            df = pd.read_excel(BytesIO(file_bytes))
        elif file_type == 'json':
            import json
            data = json.loads(file_bytes)
            df = pd.DataFrame(data)
        else:
            raise ValueError("Unsupported file type")
        result = schemas.BulkImportResult(total_rows=len(df), imported=0, skipped=0, errors=[])
        for idx, row in df.iterrows():
            try:
                # Mapping: subject_id is required, etc.
                qdata = schemas.QuestionCreate(
                    subject_id=UUID(str(row['subject_id'])),
                    topic_id=UUID(str(row['topic_id'])) if pd.notna(row.get('topic_id')) else None,
                    question_type=row['question_type'],
                    difficulty=row.get('difficulty', 'medium'),
                    question_text=row['question_text'],
                    options=eval(row['options']) if pd.notna(row.get('options')) else None,
                    correct_answer=str(row.get('correct_answer', '')),
                    marks=int(row.get('marks', 1)),
                    negative_marks=float(row.get('negative_marks', 0)),
                    bloom_level=row.get('bloom_level'),
                    tags=eval(row.get('tags', '[]')) if pd.notna(row.get('tags')) else []
                )
                await self.create_question(qdata, created_by)
                result.imported += 1
            except Exception as e:
                result.skipped += 1
                result.errors.append(f"Row {idx}: {str(e)}")
        return result
    
    async def export_questions(self, filters: dict, file_format: str) -> bytes:
        """Export questions as JSON, CSV, or Excel."""
        questions = await self.list_questions(
            subject_id=filters.get('subject_id'),
            topic_id=filters.get('topic_id'),
            difficulty=filters.get('difficulty'),
            question_type=filters.get('question_type'),
            skip=0,
            limit=10000
        )
        data = [{
            "id": str(q.id),
            "subject_id": str(q.subject_id),
            "topic_id": str(q.topic_id) if q.topic_id else "",
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "marks": q.marks,
            "negative_marks": float(q.negative_marks),
            "bloom_level": q.bloom_level,
            "tags": q.tags,
        } for q in questions]
        if file_format == "json":
            return json.dumps(data, indent=2).encode()
        elif file_format == "csv":
            import pandas as pd
            df = pd.DataFrame(data)
            return df.to_csv(index=False).encode()
        elif file_format == "xlsx":
            import pandas as pd
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df = pd.DataFrame(data)
                df.to_excel(writer, index=False, sheet_name='Questions')
            return output.getvalue()
        else:
            raise ValueError("Unsupported format")