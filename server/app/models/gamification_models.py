from sqlalchemy import Column, String, Integer, DateTime, Date, Boolean, JSON, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
import uuid
from app.models.base import EdVenturaBase

class GamificationStreak(EdVenturaBase):
    __tablename__ = "gamification_streaks"
    user_id = Column(UUID, nullable=False)
    user_type = Column(String(20), nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_attendance_date = Column(Date)

class GamificationPoints(EdVenturaBase):
    __tablename__ = "gamification_points"
    user_id = Column(UUID, nullable=False)
    user_type = Column(String(20), nullable=False)
    balance = Column(Integer, default=0)

class GamificationBadge(EdVenturaBase):
    __tablename__ = "gamification_badges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    user_id = Column(UUID, nullable=False)
    user_type = Column(String(20), nullable=False)
    badge_code = Column(String(50), nullable=False)
    awarded_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class GamificationInventory(EdVenturaBase):
    __tablename__ = "gamification_inventory"
    name = Column(String(100), nullable=False)
    description = Column(Text)
    cost_points = Column(Integer, nullable=False)
    quantity_available = Column(Integer, default=1)
    image_url = Column(String(255))
    is_active = Column(Boolean, default=True)

class GamificationRedemption(EdVenturaBase):
    __tablename__ = "gamification_redemptions"
    user_id = Column(UUID, nullable=False)
    item_id = Column(UUID, nullable=False)
    points_spent = Column(Integer, nullable=False)
    redeemed_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class GamificationTournament(EdVenturaBase):
    __tablename__ = "gamification_tournaments"
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    type = Column(String(20), nullable=False)
    scoring_config = Column(JSON, default={})

class GamificationTournamentScore(EdVenturaBase):
    __tablename__ = "gamification_tournament_scores"
    tournament_id = Column(UUID, nullable=False)
    entity_id = Column(UUID, nullable=False)
    score = Column(Numeric(10,2), default=0)
    calculated_at = Column(DateTime(timezone=True), server_default=sa.func.now())

class GamificationSocialFeed(EdVenturaBase):
    __tablename__ = "gamification_social_feed"
    user_id = Column(UUID, nullable=True)
    content = Column(Text, nullable=False)
    post_type = Column(String(30), default='milestone')

class OnlineSessionLog(EdVenturaBase):
    __tablename__ = "online_session_logs"
    student_id = Column(UUID, nullable=False)
    session_id = Column(String(100), nullable=False)
    join_time = Column(DateTime(timezone=True))
    leave_time = Column(DateTime(timezone=True))
    watch_percentage = Column(Numeric(5,2))
    engagement_metrics = Column(JSON, default={})

class RiskScore(EdVenturaBase):
    __tablename__ = "risk_scores"
    student_id = Column(UUID, nullable=False)
    attendance_risk = Column(Numeric(5,2))
    academic_risk = Column(Numeric(5,2))
    behavior_risk = Column(Numeric(5,2))
    composite_risk = Column(Numeric(5,2))
    factors = Column(JSON, default={})

class ForecastModel(EdVenturaBase):
    __tablename__ = "forecast_models"
    class_id = Column(UUID, nullable=True)
    model_path = Column(String(255))
    accuracy = Column(Numeric(5,2))
    trained_at = Column(DateTime(timezone=True))

class VoiceCommandLog(EdVenturaBase):
    __tablename__ = "voice_command_logs"
    user_id = Column(UUID, nullable=False)
    command_text = Column(Text, nullable=False)
    response = Column(Text)
    
    

