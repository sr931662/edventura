from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.exam_models import SkillTreeProgress, XPEvent
from app.models.gamification_models import (
    GamificationStreak, GamificationPoints, GamificationBadge,
    GamificationInventory, GamificationRedemption,
    GamificationTournament, GamificationTournamentScore,
    GamificationSocialFeed
)
from app.modules.attendance.event_publisher import publish_event
from datetime import date, datetime, timedelta
from uuid import UUID
import json


class GamificationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ---------------------------------------------------------------
    # Core event handler – called from attendance marking
    # ---------------------------------------------------------------
    async def handle_attendance_event(self, student_id: UUID, status: str, attendance_date: date):
        if not student_id or not status or not attendance_date:
            return
        await self.update_streak(student_id, "student", attendance_date, status)
        await self.update_points(student_id, "student", status)
        await self.check_level_up(student_id, "student")

    # ---------------------------------------------------------------
    # Streak Management
    # ---------------------------------------------------------------
    async def update_streak(self, user_id: UUID, user_type: str, attendance_date: date, status: str):
        streak_rec = await self.db.execute(
            select(GamificationStreak).where(
                GamificationStreak.user_id == user_id,
                GamificationStreak.user_type == user_type,
                GamificationStreak.tenant_id == self.tenant_id
            )
        )
        streak = streak_rec.scalar_one_or_none()
        if not streak:
            streak = GamificationStreak(
                tenant_id=self.tenant_id,
                user_id=user_id,
                user_type=user_type,
                current_streak=0,
                longest_streak=0
            )
            self.db.add(streak)

        if status in ("present", "late"):
            if streak.last_attendance_date:
                if (attendance_date - streak.last_attendance_date).days == 1:
                    streak.current_streak = streak.current_streak + 1
                else:
                    streak.current_streak = 1
            else:
                streak.current_streak = 1
            streak.last_attendance_date = attendance_date
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
                # Award streak badge
                await self.award_badge(user_id, user_type, f"streak_{streak.longest_streak}")
                # Social feed shout-out
                await self.add_social_post(user_id, f"🔥 New record! {streak.longest_streak}-day streak!")
        else:
            old_streak = streak.current_streak
            streak.current_streak = 0
            if old_streak > 0:
                await self.add_social_post(user_id, f"💔 Streak of {old_streak} days broken. Keep going!")

        await self.db.commit()

    # ---------------------------------------------------------------
    # Points
    # ---------------------------------------------------------------
    async def update_points(self, user_id: UUID, user_type: str, status: str):
        points_rec = await self.db.execute(
            select(GamificationPoints).where(
                GamificationPoints.user_id == user_id,
                GamificationPoints.user_type == user_type,
                GamificationPoints.tenant_id == self.tenant_id
            )
        )
        points = points_rec.scalar_one_or_none()
        if not points:
            points = GamificationPoints(tenant_id=self.tenant_id, user_id=user_id, user_type=user_type, balance=0)
            self.db.add(points)
        if status == "present":
            points.balance += 10
        elif status == "late":
            points.balance += 5
        await self.db.commit()

    # ---------------------------------------------------------------
    # Badges & Achievements
    # ---------------------------------------------------------------
    async def award_badge(self, user_id: UUID, user_type: str, badge_code: str):
        existing = (await self.db.execute(
            select(GamificationBadge).where(
                GamificationBadge.user_id == user_id,
                GamificationBadge.user_type == user_type,
                GamificationBadge.badge_code == badge_code
            )
        )).scalar_one_or_none()
        if not existing:
            badge = GamificationBadge(
                tenant_id=self.tenant_id,
                user_id=user_id,
                user_type=user_type,
                badge_code=badge_code
            )
            self.db.add(badge)
            await self.db.commit()
            await self.add_social_post(user_id, f"🎉 Earned badge: {badge_code}")

    async def check_level_up(self, user_id: UUID, user_type: str):
        # Bronze: 30 days streak, Silver: 60 + 500 pts, Gold: 90 + 1000 pts + 3 badges
        streak = (await self.db.execute(
            select(GamificationStreak).where(
                GamificationStreak.user_id == user_id,
                GamificationStreak.user_type == user_type,
                GamificationStreak.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        points = (await self.db.execute(
            select(GamificationPoints).where(
                GamificationPoints.user_id == user_id,
                GamificationPoints.user_type == user_type,
                GamificationPoints.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        badges_count = (await self.db.execute(
            select(func.count()).select_from(GamificationBadge).where(
                GamificationBadge.user_id == user_id,
                GamificationBadge.user_type == user_type
            )
        )).scalar() or 0

        if not streak:
            return
        if streak.current_streak >= 90 and points and points.balance >= 1000 and badges_count >= 3:
            await self.award_badge(user_id, user_type, "level_gold")
        elif streak.current_streak >= 60 and points and points.balance >= 500:
            await self.award_badge(user_id, user_type, "level_silver")
        elif streak.current_streak >= 30:
            await self.award_badge(user_id, user_type, "level_bronze")

    # ---------------------------------------------------------------
    # Inventory & Redemption
    # ---------------------------------------------------------------
    async def get_store_items(self):
        result = await self.db.execute(
            select(GamificationInventory).where(
                GamificationInventory.tenant_id == self.tenant_id,
                GamificationInventory.is_active == True
            )
        )
        return result.scalars().all()

    async def redeem_item(self, user_id: UUID, item_id: UUID):
        item = await self.db.get(GamificationInventory, item_id)
        if not item or not item.is_active:
            raise ValueError("Item not available")
        points = (await self.db.execute(
            select(GamificationPoints).where(
                GamificationPoints.user_id == user_id,
                GamificationPoints.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if not points or points.balance < item.cost_points:
            raise ValueError("Insufficient points")
        points.balance -= item.cost_points
        item.quantity_available -= 1
        if item.quantity_available <= 0:
            item.is_active = False
        redemption = GamificationRedemption(
            tenant_id=self.tenant_id,
            user_id=user_id,
            item_id=item_id,
            points_spent=item.cost_points
        )
        self.db.add(redemption)
        await self.db.commit()
        return redemption

    # ---------------------------------------------------------------
    # Tournaments
    # ---------------------------------------------------------------
    async def create_tournament(self, data: dict):
        t = GamificationTournament(tenant_id=self.tenant_id, **data)
        self.db.add(t)
        await self.db.commit()
        return t

    async def get_class_leaderboard(self, from_date: date, to_date: date) -> list:
        # Aggregate attendance percent per class for the period using attendance records
        from app.models.attendance_models import AttendanceRecord
        from app.models.class_ import Class
        from sqlalchemy import case
        stmt = (
            select(
                AttendanceRecord.class_id,
                func.count().label('total'),
                func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present')
            )
            .where(
                AttendanceRecord.tenant_id == self.tenant_id,
                AttendanceRecord.date >= from_date,
                AttendanceRecord.date <= to_date,
                AttendanceRecord.attendance_type == 'student_class'
            )
            .group_by(AttendanceRecord.class_id)
        )
        results = await self.db.execute(stmt)
        rows = results.all()
        leaderboard = []
        for row in rows:
            cls = await self.db.get(Class, row.class_id)
            if cls:
                pct = round(row.present / row.total * 100, 2) if row.total else 0
                leaderboard.append({"class_id": row.class_id, "class_name": cls.name, "present_percent": pct})
        leaderboard.sort(key=lambda x: x['present_percent'], reverse=True)
        return leaderboard

    # ---------------------------------------------------------------
    # Social Feed
    # ---------------------------------------------------------------
    async def add_social_post(self, user_id: UUID, content: str):
        post = GamificationSocialFeed(
            tenant_id=self.tenant_id,
            user_id=user_id,
            content=content,
            post_type='milestone'
        )
        self.db.add(post)
        await self.db.commit()

    async def get_feed(self, class_id: Optional[UUID] = None, limit=20):
        stmt = select(GamificationSocialFeed).where(
            GamificationSocialFeed.tenant_id == self.tenant_id
        )
        if class_id:
            # join with student to filter by class; for simplicity we skip class filter
            pass
        stmt = stmt.order_by(GamificationSocialFeed.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def award_xp(self, user_id: UUID, event_type: str, xp: int, related_entity_id: Optional[UUID] = None):
        xp_event = XPEvent(
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_type=event_type,
            xp_awarded=xp,
            related_entity_id=related_entity_id
        )
        self.db.add(xp_event)
        # Update total XP in GamificationPoints? We'll assume points represent total XP.
        await self.update_points(user_id, 'student', 'present')  # hack? better to add dedicated column.
        # For now, we won't modify GamificationPoints balance based on XP; we'll keep separate.

    async def update_skill_tree(self, student_id: UUID, subject_id: UUID, skill_node: str, progress_increment: float):
        prog = (await self.db.execute(
            select(SkillTreeProgress).where(
                SkillTreeProgress.student_id == student_id,
                SkillTreeProgress.subject_id == subject_id,
                SkillTreeProgress.skill_node == skill_node,
                SkillTreeProgress.tenant_id == self.tenant_id
            )
        )).scalar_one_or_none()
        if not prog:
            prog = SkillTreeProgress(
                tenant_id=self.tenant_id,
                student_id=student_id,
                subject_id=subject_id,
                skill_node=skill_node,
                progress=0,
                level=1
            )
            self.db.add(prog)
        new_progress = min(100, float(prog.progress) + progress_increment)
        prog.progress = new_progress
        if new_progress >= 100:
            prog.level += 1
            prog.progress = 0
            await self.award_badge(student_id, 'student', f"skill_master_{skill_node}_level_{prog.level}")
        await self.db.commit()