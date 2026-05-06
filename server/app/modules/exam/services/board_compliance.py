from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exam_models import ExamBoardConfig
from app.modules.exam import exam_schemas as schemas
import json

class BoardComplianceService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_board_config(self, data: dict) -> ExamBoardConfig:
        cfg = ExamBoardConfig(tenant_id=self.tenant_id, **data)
        self.db.add(cfg)
        await self.db.commit()
        return cfg

    async def list_board_configs(self) -> list:
        stmt = select(ExamBoardConfig).where(ExamBoardConfig.tenant_id == self.tenant_id, ExamBoardConfig.is_deleted == False)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_grading(self, board_name: str) -> dict:
        cfg = await self.db.execute(
            select(ExamBoardConfig).where(
                ExamBoardConfig.tenant_id == self.tenant_id,
                ExamBoardConfig.board_name == board_name,
                ExamBoardConfig.is_deleted == False
            )
        )
        cfg = cfg.scalar_one_or_none()
        if cfg and cfg.grading_system:
            return json.loads(cfg.grading_system) if isinstance(cfg.grading_system, str) else cfg.grading_system
        return {}

    async def calculate_grade(self, board_name: str, percentage: float) -> str:
        grading = await self.get_grading(board_name)
        if not grading:
            return "NA"
        # grading is assumed to be { "A1": [91,100], "A2": [81,90], ... }
        for grade, (low, high) in grading.items():
            if low <= percentage <= high:
                return grade
        return "F"