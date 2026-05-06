#!/usr/bin/env python3
"""
EdVentura Demo School Seeder
Creates two fully isolated demo schools, each with all 26 roles and one demo
user per role.  Safe to run multiple times (skips existing records).

Usage:
    python scripts/seed_demo_schools.py
"""

import asyncio
import sys
import os
import uuid as uuid_mod

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.core.database import async_session_factory, engine, Base
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.user_role import user_roles
# Import all models so Base.metadata is complete before create_all
import app.models.user
import app.models.role
import app.models.permission
import app.models.role_permission
import app.models.user_role
import app.models.tenant
import app.models.student
import app.models.class_
import app.models.communication_models
import app.models.gamification_models
import app.models.attendance_models
import app.models.finance_models
import app.models.exam_models

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

# (email_prefix, full_name, role_name)
# email will be: {prefix}@{school_domain}
DEMO_USERS = [
    ("owner",           "Institution Owner",    "Institution Owner"),
    ("leader",          "Institution Leader",   "Institution Leader"),
    ("admin",           "Institution Admin",    "Institution Admin"),
    ("subadmin",        "Sub Admin",            "Sub-Admin"),
    ("registrar",       "Registrar",            "Registrar"),
    ("accountant",      "Accountant",           "Accountant"),
    ("financehead",     "Finance Head",         "Finance Head"),
    ("hod",             "Head of Dept",         "HOD"),
    ("teacher",         "Teacher",              "Teacher"),
    ("student",         "Student",              "Student"),
    ("parent",          "Parent",               "Parent"),
    ("librarian",       "Librarian",            "Librarian"),
    ("examcontroller",  "Exam Controller",      "Exam Controller"),
    ("admcounsellor",   "Admission Counsellor", "Admission Counsellor"),
    ("coordinator",     "Academic Coordinator", "Academic Coordinator"),
    ("classteacher",    "Class Teacher",        "Class Teacher"),
    ("transport",       "Transport Manager",    "Transport Manager"),
    ("hostel",          "Hostel Manager",       "Hostel Manager"),
    ("hr",              "HR Manager",           "HR Manager"),
    ("ithead",          "IT Head",              "IT Head"),
    ("counsellor",      "Counsellor",           "Counsellor"),
    ("medical",         "Medical Staff",        "Medical Staff"),
    ("activity",        "Activity Coordinator", "Activity Coordinator"),
    ("coach",           "Sports Coach",         "Sports Coach"),
    ("vendor",          "Vendor",               "Vendor"),
]

DEMO_SCHOOLS = [
    {"name": "Sunrise Academy",  "domain": "sunrise.demo"},
    {"name": "Greenfield School", "domain": "greenfield.demo"},
]

DEMO_PASSWORD = "Demo@2026"


async def _get_or_create_tenant(session, name: str, domain: str) -> Tenant:
    existing = await session.scalar(select(Tenant).where(Tenant.domain == domain))
    if existing:
        print(f"  ℹ️  Tenant already exists: {name}")
        return existing
    tid = uuid_mod.uuid4()
    tenant = Tenant(name=name, domain=domain)
    tenant.id = tid
    tenant.tenant_id = tid  # self-referential: Tenant owns itself
    session.add(tenant)
    await session.flush()
    print(f"  ✅ Created tenant: {name} (id={tenant.id})")
    return tenant


async def _get_system_roles(session) -> dict[str, Role]:
    """Roles are global system records shared across tenants."""
    roles = (await session.execute(
        select(Role).where(Role.name.in_(ROLE_NAMES))
    )).scalars().all()
    found = {r.name: r for r in roles}
    missing = set(ROLE_NAMES) - found.keys()
    if missing:
        print(f"    ⚠️  Missing system roles (run seed.py first): {missing}")
    return found



async def _create_demo_users(session, tenant: Tenant, roles: dict[str, Role]):
    for prefix, full_name, role_name in DEMO_USERS:
        email = f"{prefix}@{tenant.domain}"
        existing = await session.scalar(select(User).where(User.email == email))
        if existing:
            print(f"    ℹ️  User already exists: {email}")
            continue
        role = roles.get(role_name)
        if not role:
            print(f"    ⚠️  Role not found: {role_name}, skipping {email}")
            continue
        user = User(
            email=email,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name=f"{full_name} ({tenant.name})",
            is_active=True,
            tenant_id=tenant.id,
        )
        session.add(user)
        await session.flush()
        await session.execute(
            insert(user_roles).values(
                user_id=user.id,
                role_id=role.id,
                tenant_id=tenant.id,
            ).on_conflict_do_nothing()
        )
        print(f"    ✅ {email}  →  {role_name}")


OLD_SCHEMA_TABLES = [
    # Old schema tables that conflict with the new EdVentura schema.
    # Dropped in an order that respects FK dependencies (CASCADE handles the rest).
    "institute_documents",
    "institute_subscriptions",
    "institute_verifications",
    "branches",
    "subscription_plans",
    "institutions",
    "users",           # old integer-id users — must go before create_all
    "alembic_version",
]

async def _has_old_schema(conn) -> bool:
    """Returns True if the users table exists with an integer (old) primary key."""
    from sqlalchemy import text
    result = await conn.execute(text(
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name='users' AND column_name='id' AND table_schema='public'"
    ))
    row = result.fetchone()
    return row is not None and row[0] in ("integer", "bigint", "smallint")


async def _drop_old_tables(conn):
    from sqlalchemy import text
    for table in OLD_SCHEMA_TABLES:
        await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
        print(f"  🗑️  Dropped old table (if existed): {table}")


async def seed():
    async with engine.begin() as conn:
        if await _has_old_schema(conn):
            print("🔧 Old schema detected — dropping old tables and creating EdVentura schema…")
            await _drop_old_tables(conn)
        else:
            print("🔧 Creating EdVentura schema (if not exists)…")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Schema ready.\n")

    async with async_session_factory() as session:
        for school in DEMO_SCHOOLS:
            print(f"\n🏫  Seeding: {school['name']} ({school['domain']})")
            tenant = await _get_or_create_tenant(session, school["name"], school["domain"])
            await session.commit()

            print("  📋 Fetching system roles…")
            roles = await _get_system_roles(session)

            print("  👤 Creating demo users…")
            await _create_demo_users(session, tenant, roles)
            await session.commit()

        print(f"\n🎉 Done!  Login password for all demo users: {DEMO_PASSWORD}")
        print("\nDemo accounts summary:")
        for school in DEMO_SCHOOLS:
            print(f"\n  {school['name']} (domain: {school['domain']})")
            for prefix, _, role in DEMO_USERS:
                print(f"    {prefix}@{school['domain']}  →  {role}")


if __name__ == "__main__":
    asyncio.run(seed())
