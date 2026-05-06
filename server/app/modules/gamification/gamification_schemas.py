from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, time, datetime
from uuid import UUID
from fastapi import UploadFile

# Attendance

# Gamification
class StreakOut(BaseModel):
    user_id: UUID
    current_streak: int
    longest_streak: int
    class Config: from_attributes = True

class PointsOut(BaseModel):
    user_id: UUID
    balance: int

class BadgeOut(BaseModel):
    badge_code: str
    awarded_at: datetime

class InventoryItemOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    cost_points: int
    quantity_available: int
    image_url: Optional[str]

class RedeemRequest(BaseModel):
    item_id: UUID

class TournamentCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    type: str
    scoring_config: Optional[dict] = {}

class TournamentOut(BaseModel):
    id: UUID
    name: str
    type: str
    start_date: date
    end_date: date

class TournamentLeaderboard(BaseModel):
    entity_id: UUID
    entity_name: str
    score: float

# AI
class RiskScoreOut(BaseModel):
    student_id: UUID
    composite_risk: float
    attendance_risk: float
    academic_risk: float
    behavior_risk: float
    factors: dict

class EngagementPayload(BaseModel):
    session_id: str
    student_id: UUID
    mouse_movements: int = 0
    keystrokes: int = 0
    camera_frame: Optional[str] = None   # base64 optional

class EngagementResult(BaseModel):
    score: float
    disengaged: bool

class VoiceCommandRequest(BaseModel):
    audio_file: Optional[UploadFile] = None   # but in JSON we use text for simplicity
    text_command: Optional[str] = None

class VoiceTaskOut(BaseModel):
    task_id: UUID
    status: str

class ForecastOut(BaseModel):
    date: date
    predicted_percent: float

class CorrelationResult(BaseModel):
    coefficient: float
    p_value: float
    data: List[dict]