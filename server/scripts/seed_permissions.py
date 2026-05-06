import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import async_session_factory
from app.models.role import Role
from app.models.permission import Permission
from app.models.tenant import Tenant
from app.models.role_permission import role_permissions
from sqlalchemy import select, insert

# 1. Define all permissions (codenames)
PERMISSIONS_LIST = {
    # Institution Management
    "tenant:read": "View institution details",
    "tenant:write": "Modify institution settings",
    "tenant:onboard": "Onboard new institution",
    "tenant:delete": "Delete institution",
    # User & RBAC
    "user:read": "View users",
    "user:create": "Create users",
    "user:update": "Edit users",
    "user:delete": "Delete users",
    "role:read": "View roles",
    "role:create": "Create roles",
    "role:update": "Edit roles",
    "role:delete": "Delete roles",
    "permission:assign": "Assign permissions to roles",
    # Student Management
    "student:read": "View student profiles",
    "student:create": "Add new student",
    "student:update": "Update student info",
    "student:delete": "Remove student",
    "student:bulk": "Bulk operations (promote, import)",
    # Academic / Course
    "course:read": "View courses",
    "course:create": "Create courses",
    "course:update": "Update courses",
    "course:delete": "Delete courses",
    "subject:read": "View subjects",
    "subject:create": "Create subjects",
    "subject:update": "Update subjects",
    "subject:delete": "Delete subjects",
    "syllabus:read": "View syllabus",
    "syllabus:create": "Create syllabus",
    "syllabus:update": "Update syllabus",
    "syllabus:delete": "Delete syllabus",
    "class:read": "View classes/sections",
    "class:create": "Create classes",
    "class:update": "Update classes",
    "class:delete": "Delete classes",
    "timetable:read": "View timetable",
    "timetable:create": "Create timetable",
    "timetable:update": "Update timetable",
    "timetable:delete": "Delete timetable",
    # Attendance
    "attendance:read": "View attendance records",
    "attendance:write": "Mark/edit attendance",
    "attendance:bulk": "Bulk attendance operations",
    # Exams & Assessments
    "exam:read": "View exam schedules/results",
    "exam:create": "Create exams",
    "exam:update": "Update exams",
    "exam:delete": "Delete exams",
    "exam:evaluate": "Evaluate answer sheets",
    "exam:publish": "Publish results",
    "assignment:read": "View assignments",
    "assignment:create": "Create assignments",
    "assignment:submit": "Submit assignment",
    "assignment:grade": "Grade assignments",
    # Exam & Assessment
    "subject:read": "View subjects",
    "subject:create": "Create subjects",
    "subject:update": "Update subjects",
    "subject:delete": "Delete subjects",
    "question:read": "View questions",
    "question:create": "Create questions",
    "question:update": "Update questions",
    "question:delete": "Delete questions",
    "blueprint:read": "View exam blueprints",
    "blueprint:create": "Create blueprints",
    "blueprint:update": "Update blueprints",
    "blueprint:delete": "Delete blueprints",
    "exam:read": "View exams",
    "exam:create": "Create exams",
    "exam:update": "Update exams",
    "exam:delete": "Delete exams",
    "system:read": "View system features",
    "system:write": "Toggle system features",
    "exam:approve": "Approve exams",
    "exam:reject": "Reject exams",
    "exam:moderate": "Moderate exam papers",
    "exam:schedule": "Schedule exams and halls",
    # Fee & Finance
    "fee:read": "View fee records",
    "fee:create": "Create fee structures",
    "fee:update": "Edit fee structures",
    "fee:delete": "Delete fee structures",
    "fee:collect": "Record payments",
    "finance:read": "View financial reports",
    "finance:write": "Manage ledgers/transactions",
    "finance:reconcile": "Reconcile accounts",
    "finance:approve": "Approve financial operations",
    # Communication
    "communication:send": "Send messages/announcements",
    "communication:read": "Read messages",
    # Library
    "library:read": "Browse catalog",
    "library:manage": "Manage books/circulation",
    # Transport
    "transport:read": "View transport details",
    "transport:manage": "Manage routes/vehicles",
    # Hostel
    "hostel:read": "View hostel info",
    "hostel:manage": "Manage hostel operations",
    # HR
    "hr:read": "View employee records",
    "hr:write": "Manage employees",
    "hr:payroll": "Process payroll",
    # IT / System
    "system:read": "View system config",
    "system:write": "Modify system settings",
    # AI & Insights
    "insights:view": "View AI insights",
    "insights:configure": "Configure AI modules",
    # Vendor
    "vendor:read": "View vendor details",
    "vendor:manage": "Manage vendor relationships",
    # General
    "feedback:manage": "Manage feedback",
    "complaint:manage": "Manage complaints",
    "document:read": "View documents",
    "document:manage": "Upload/edit documents",
    "certificate:generate": "Generate certificates",
    "admission:read": "View admission pipeline",
    "admission:manage": "Process applications",
    "gamification:manage": "Manage gamification",
    "communication:read": "View communications",
    "communication:send": "Send communications",
    "communication:write": "Create/update communication templates",
    "communication:admin": "Manage communication settings",
}

# 2. Map roles to permissions (based on SRS feature tables)
ROLE_PERMISSION_MAP = {
    "Institution Owner": [
        "tenant:onboard", "tenant:read", "tenant:write", "tenant:delete",
        "user:read", "user:create", "user:update", "user:delete",
        "role:read", "role:create", "role:update", "role:delete", "permission:assign",
        "student:read", "course:read", "subject:read", "class:read",
        "attendance:read", "exam:read", "fee:read", "finance:read", "finance:approve",
        "communication:send", "communication:read",
        "library:read", "transport:read", "hostel:read",
        "hr:read", "system:read", "insights:view", "vendor:read",
        "feedback:manage", "complaint:manage", "document:read",
        "admission:read", "gamification:manage"
    ],
    "Institution Leader": [
        "tenant:read", "user:read",
        "student:read", "student:create", "student:update", "student:delete",
        "course:read", "course:create", "course:update", "course:delete",
        "subject:read", "subject:create", "subject:update", "subject:delete",
        "syllabus:read", "syllabus:create", "syllabus:update", "syllabus:delete",
        "class:read", "class:create", "class:update", "class:delete",
        "timetable:read", "timetable:create", "timetable:update",
        "attendance:read", "attendance:write",
        "exam:read", "exam:create", "exam:update", "exam:evaluate", "exam:publish",
        "assignment:read", "assignment:create", "assignment:grade",
        "fee:read", "finance:read",
        "communication:send", "communication:read",
        "library:read", "transport:read", "hostel:read",
        "hr:read", "insights:view",
        "feedback:manage", "complaint:manage", "document:read",
        "admission:read", "gamification:manage"
    ],
    "Institution Admin": [
        "tenant:read", "user:read", "user:create", "user:update",
        "role:read",  # can assign existing roles, but not create new ones
        "student:read", "student:create", "student:update", "student:delete",
        "course:read", "course:create", "course:update", "course:delete",
        "subject:read", "subject:create", "subject:update", "subject:delete",
        "syllabus:read", "syllabus:create", "syllabus:update", "syllabus:delete",
        "class:read", "class:create", "class:update", "class:delete",
        "timetable:read", "timetable:create", "timetable:update",
        "attendance:read", "attendance:write", "attendance:bulk",
        "exam:read", "exam:create", "exam:update", "exam:evaluate", "exam:publish",
        "assignment:read", "assignment:create", "assignment:grade",
        "fee:read", "fee:create", "fee:update", "fee:collect",
        "finance:read", "finance:write", "finance:reconcile",
        "communication:send", "communication:read",
        "library:read", "library:manage",
        "transport:read", "transport:manage",
        "hostel:read", "hostel:manage",
        "hr:read", "hr:write",  # can process HR tasks
        "system:read",  # limited
        "insights:view",
        "vendor:read", "vendor:manage",
        "feedback:manage", "complaint:manage", "document:manage",
        "certificate:generate",
        "admission:read", "admission:manage",
        "gamification:manage"
    ],
    "Sub-Admin": [
        # Scoped domain-specific permissions; assume minimal common set
        "student:read", "student:create", "student:update",
        "attendance:read", "attendance:write",
        "exam:read", "assignment:read", "assignment:submit",
        "fee:read", "fee:collect",
        "communication:send", "communication:read",
        "library:read", "transport:read", "hostel:read",
        "hr:read", "vendor:read",
        "document:read", "admission:read"
    ],
    "Registrar": [
        "student:read", "student:create", "student:update", "student:delete", "student:bulk",
        "document:manage", "certificate:generate",
        "class:read", "class:update",
        "admission:read", "admission:manage",
        "communication:send", "communication:read",
        "compliance:manage"  # we'll add a compliance permission if needed
    ],
    "Accountant": [
        "fee:read", "fee:create", "fee:update", "fee:collect",
        "finance:read", "finance:write", "finance:reconcile",
        "communication:send", "communication:read",
        "document:read",
        "insights:view"
    ],
    "Finance Head": [
        "fee:read", "fee:create", "fee:update", "fee:delete",
        "finance:read", "finance:write", "finance:reconcile", "finance:approve",
        "fee:collect",
        "communication:send", "communication:read",
        "document:read",
        "insights:view", "insights:configure"
    ],
    "HOD": [
        "student:read", "student:update",
        "course:read", "subject:read",
        "syllabus:read", "syllabus:create", "syllabus:update",
        "class:read",
        "timetable:read",
        "attendance:read", "attendance:write",
        "exam:read", "exam:create", "exam:update", "exam:evaluate", "exam:publish",
        "assignment:read", "assignment:create", "assignment:grade",
        "communication:send", "communication:read",
        "insights:view",
        "feedback:manage"
    ],
    "Teacher": [
        "student:read",
        "attendance:read", "attendance:write",
        "assignment:read", "assignment:create", "assignment:grade",
        "exam:read", "exam:evaluate",
        "communication:send", "communication:read",
        "syllabus:read",
        "class:read",
        "insights:view"  # limited
    ],
    "Student": [
        "student:read",  # own profile
        "assignment:read", "assignment:submit",
        "exam:read",
        "attendance:read",
        "course:read", "subject:read",
        "syllabus:read",
        "class:read",
        "timetable:read",
        "library:read",
        "communication:send", "communication:read",
        "document:read"
    ],
    "Parent": [
        "student:read",  # children's info
        "attendance:read",
        "exam:read",
        "assignment:read",
        "fee:read",
        "communication:send", "communication:read",
        "document:read",
        "insights:view"
    ],
    "Librarian": [
        "library:read", "library:manage",
        "document:manage",
        "communication:send", "communication:read"
    ],
    "Exam Controller": [
        "exam:read", "exam:create", "exam:update", "exam:delete", "exam:evaluate", "exam:publish",
        "assignment:read",
        "communication:send", "communication:read",
        "certificate:generate",
        "document:read",
        "insights:view"
    ],
    "Admission Counsellor": [
        "admission:read", "admission:manage",
        "communication:send", "communication:read",
        "student:read", "student:create",
        "document:read",
        "insights:view"
    ],
    "Academic Coordinator": [
        "timetable:read", "timetable:create", "timetable:update",
        "syllabus:read",
        "class:read",
        "attendance:read",
        "communication:send", "communication:read",
        "assignment:read",
        "exam:read",
        "insights:view"
    ],
    "Class Teacher": [
        "student:read", "student:update",
        "attendance:read", "attendance:write",
        "communication:send", "communication:read",
        "assignment:read",
        "exam:read",
        "class:read",
        "feedback:manage"
    ],
    "Transport Manager": [
        "transport:read", "transport:manage",
        "student:read",  # assigned students
        "communication:send", "communication:read",
        "fee:read",
        "insights:view"
    ],
    "Hostel Manager": [
        "hostel:read", "hostel:manage",
        "student:read",
        "communication:send", "communication:read",
        "fee:read",
        "insights:view"
    ],
    "HR Manager": [
        "hr:read", "hr:write", "hr:payroll",
        "user:read",
        "communication:send", "communication:read",
        "document:manage",
        "insights:view"
    ],
    "IT Head": [
        "system:read", "system:write",
        "user:read",
        "communication:read",
        "insights:view"
    ],
    "Counsellor": [
        "student:read", "student:update",
        "communication:send", "communication:read",
        "document:read",
        "insights:view"
    ],
    "Medical Staff": [
        "student:read",
        "document:manage",
        "communication:send", "communication:read",
        "insights:view"
    ],
    "Activity Coordinator": [
        "student:read",
        "communication:send", "communication:read",
        "gamification:manage",
        "insights:view"
    ],
    "Sports Coach": [
        "student:read",
        "communication:send", "communication:read",
        "attendance:read", "attendance:write",
        "insights:view"
    ],
    "Vendor": [
        "vendor:read",
        "document:read",
        "communication:send", "communication:read",
        "fee:read"
    ],
}

async def seed():
    async with async_session_factory() as session:
        # Get default tenant
        tenant = (await session.execute(select(Tenant).limit(1))).scalar_one_or_none()
        if not tenant:
            print("No tenant found. Run seed.py first.")
            return

        # Create permissions
        for codename, desc in PERMISSIONS_LIST.items():
            # check if exists
            existing = (await session.execute(select(Permission).where(Permission.codename == codename))).scalar_one_or_none()
            if not existing:
                session.add(Permission(codename=codename, description=desc, tenant_id=tenant.id))
        await session.commit()

        # Assign permissions to roles
        for role_name, perms in ROLE_PERMISSION_MAP.items():
            role = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one_or_none()
            if not role:
                print(f"Role {role_name} not found, skipping")
                continue
            # fetch permission IDs
            pids = (await session.execute(select(Permission.id).where(Permission.codename.in_(perms)))).scalars().all()
            # insert using raw text to avoid duplicates
            for pid in pids:
                stmt = role_permissions.insert().values(role_id=role.id, permission_id=pid).prefix_with("or ignore")
                # For PostgreSQL use ON CONFLICT DO NOTHING
                # We'll construct a proper insert with on_conflict_do_nothing
                from sqlalchemy.dialects.postgresql import insert as pg_insert
                ins = pg_insert(role_permissions).values(role_id=role.id, permission_id=pid).on_conflict_do_nothing()
                await session.execute(ins)
            await session.commit()
        print("Permissions seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())