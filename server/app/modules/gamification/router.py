from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_tenant
from app.models.gamification_models import GamificationStreak
from app.modules.gamification.gamification_service import GamificationService
from app.modules.gamification.gamification_schemas import (
    StreakOut, PointsOut, BadgeOut, InventoryItemOut,
    RedeemRequest, TournamentCreate, TournamentOut, TournamentLeaderboard
)

router = APIRouter(prefix="/gamification", tags=["Gamification"])

async def get_gam_service(db: AsyncSession = Depends(get_db), tenant_id: str = Depends(get_current_active_tenant)) -> GamificationService:
    return GamificationService(db, UUID(tenant_id))

@router.get("/streaks/{user_id}", response_model=StreakOut)
async def get_streak(user_id: UUID, gam: GamificationService = Depends(get_gam_service)):
    streak = (await gam.db.execute(
        select(GamificationStreak).where(GamificationStreak.user_id == user_id)
    )).scalar_one_or_none()
    if not streak:
        raise HTTPException(404, "No streak found")
    return streak


@router.get("/points/{user_id}", response_model=PointsOut)
async def get_points(user_id: UUID, gam: GamificationService = Depends(get_gam_service)):
    ...

@router.get("/badges/{user_id}", response_model=list[BadgeOut])
async def get_badges(user_id: UUID, gam: GamificationService = Depends(get_gam_service)):
    ...

@router.get("/store", response_model=list[InventoryItemOut])
async def store(gam: GamificationService = Depends(get_gam_service)):
    return await gam.get_store_items()

@router.post("/redeem")
async def redeem(req: RedeemRequest, current_user = Depends(get_current_user), gam: GamificationService = Depends(get_gam_service)):
    try:
        await gam.redeem_item(current_user.id, req.item_id)
        return {"message": "Redemption successful"}
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/tournaments", response_model=TournamentOut)
async def create_tournament(data: TournamentCreate, gam: GamificationService = Depends(get_gam_service)):
    return await gam.create_tournament(data.dict())

@router.get("/leaderboard/class", response_model=list[TournamentLeaderboard])
async def class_leaderboard(from_date: date = Query(...), to_date: date = Query(...), gam: GamificationService = Depends(get_gam_service)):
    return await gam.get_class_leaderboard(from_date, to_date)

@router.get("/feed")
async def feed(limit: int = 20, gam: GamificationService = Depends(get_gam_service)):
    return await gam.get_feed(limit=limit)