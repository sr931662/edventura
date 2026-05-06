#!/usr/bin/env python3
"""
EdVentura Database Seeder
Creates:
  - Default tenant (if not exists)
  - Super admin (if not exists)
  - 26 predefined roles
  - (Optional) 25 dummy users, one for each role
Usage: python scripts/seed.py
"""

import asyncio
import sys
import os

# Add server root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import async_session_factory, engine, Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.user_role import user_roles
from sqlalchemy import select

# ------------------------------------------------------------
# Role names exactly as used in the spec (26 total, including Owner)
ROLE_NAMES = [
    "Institution Owner",
    "Institution Leader",
    "Institution Admin",
    "Sub-Admin",
    "Registrar",
    "Accountant",
    "Finance Head",
    "HOD",
    "Teacher",
    "Student",
    "Parent",
    "Librarian",
    "Exam Controller",
    "Admission Counsellor",
    "Academic Coordinator",
    "Class Teacher",
    "Transport Manager",
    "Hostel Manager",
    "HR Manager",
    "IT Head",
    "Counsellor",
    "Medical Staff",
    "Activity Coordinator",
    "Sports Coach",
    "Vendor",
]

# Dummy users for each role (password = "Test@2026")
DUMMY_USERS = [
    ("owner@rlb.demo",         "Arvind Sharma",      "Institution Owner"),
    ("leader@rlb.demo",        "Meera Iyer",         "Institution Leader"),
    ("admin@rlb.demo",         "Rajesh Kumar",       "Institution Admin"),
    ("subadmin@rlb.demo",      "Priya Nair",         "Sub-Admin"),
    ("registrar@rlb.demo",     "Deepak Reddy",       "Registrar"),
    ("accountant@rlb.demo",    "Sunita Patel",       "Accountant"),
    ("financehead@rlb.demo",   "Vivek Roy",          "Finance Head"),
    ("hod.science@rlb.demo",   "Kavita Menon",       "HOD"),
    ("teacher.math@rlb.demo",  "Amit Gupta",         "Teacher"),
    ("student1@rlb.demo",      "Riya Sen",           "Student"),
    ("parent1@rlb.demo",       "Alok Sen",           "Parent"),
    ("librarian@rlb.demo",     "Nalini Joshi",       "Librarian"),
    ("examcontroller@rlb.demo","Prakash Shetty",     "Exam Controller"),
    ("counsellor@rlb.demo",    "Anjali Das",         "Admission Counsellor"),
    ("coordinator@rlb.demo",   "Rakesh Mishra",      "Academic Coordinator"),
    ("classteacher.10A@rlb.demo","Sneha Rao",        "Class Teacher"),
    ("transport@rlb.demo",     "Vinay Singh",        "Transport Manager"),
    ("hostel@rlb.demo",        "Laxmi Bansal",       "Hostel Manager"),
    ("hr@rlb.demo",            "Sanjay Gupta",       "HR Manager"),
    ("ithead@rlb.demo",        "Karan Kapoor",       "IT Head"),
    ("counsellor@rlb.demo",    "Dr. Anju Varma",     "Counsellor"),
    ("medical@rlb.demo",       "Anita Naik",         "Medical Staff"),
    ("sports@rlb.demo",        "Hardik Patel",       "Activity Coordinator"),
    ("coach.football@rlb.demo","Mohan Lal",          "Sports Coach"),
    ("vendor1@rlb.demo",       "Green Supplies Co.", "Vendor"),
]


async def seed():
    async with async_session_factory() as session:
        # 1. Create default tenant
        result = await session.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(name="EdVentura Inc.", domain="edventura")
            session.add(tenant)
            await session.commit()
            print(f"✅ Created tenant: {tenant.name} (ID: {tenant.id})")
        else:
            print(f"ℹ️  Tenant already exists: {tenant.name} (ID: {tenant.id})")

        # 2. Create super admin
        admin_result = await session.execute(
            select(User).where(User.email == settings.SUPERADMIN_EMAIL)
        )
        admin = admin_result.scalar_one_or_none()
        if not admin:
            admin = User(
                email=settings.SUPERADMIN_EMAIL,
                hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                full_name="Super Admin",
                is_super_admin=True,
                is_active=True,
                tenant_id=tenant.id,
            )
            session.add(admin)
            await session.commit()
            print(f"✅ Created super admin: {admin.email}")
        else:
            print(f"ℹ️  Super admin already exists: {admin.email}")

        # 3. Create all roles
        existing_roles = (await session.execute(select(Role.name))).scalars().all()
        for role_name in ROLE_NAMES:
            if role_name not in existing_roles:
                role = Role(
                    name=role_name,
                    description=f"{role_name} role",
                    is_system=True,
                    tenant_id=tenant.id,
                )
                session.add(role)
                print(f"✅ Created role: {role_name}")
        await session.commit()

        # 4. Create dummy users (skip if email already exists)
        for email, full_name, role_name in DUMMY_USERS:
            existing_user = await session.scalar(
                select(User).where(User.email == email)
            )

            if existing_user:
                print(f"ℹ️  User already exists: {email}")
                continue

            # Find role
            role = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one()

            new_user = User(
                email=email,
                hashed_password=get_password_hash("Test@2026"),
                full_name=full_name,
                is_active=True,
                tenant_id=tenant.id,
            )
            session.add(new_user)

            try:
                await session.flush()  # get new_user.id
                # Assign role
                await session.execute(
                    user_roles.insert().values(
                        user_id=new_user.id,
                        role_id=role.id,
                        tenant_id=tenant.id,
                    )
                )
                await session.commit()
                print(f"✅ Created user: {new_user.email} with role {role_name}")
            except Exception as e:
                await session.rollback()
                print(f"❌ Failed to create user {email}: {e}")

        print("\n🎉 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())