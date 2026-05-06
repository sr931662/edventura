"""
Daisy – EdVentura's intelligent virtual assistant.

NLP engine  : Groq Llama 3 70B (state-of-the-art open-source LLM)
Capabilities:
  • Intent understanding (natural language)
  • Entity extraction (actions, modules, permissions)
  • Multi-turn conversation memory (injected per request)
  • Role-aware, permission-scoped guidance
  • Trilingual: English / Hindi / Hinglish
"""

import json
import logging
from typing import Optional

from groq import AsyncGroq

from app.core.config import settings
from app.modules.assistant.schemas import ChatHistoryItem, DaisyContext

log = logging.getLogger(__name__)

# ── EdVentura module catalogue injected into Daisy's knowledge ──────────────
EDVENTURA_MODULES = """
EdVentura Modules & Where To Find Them:
• Students        → Sidebar ▸ Students        (add, edit, bulk-import student records)
• Attendance      → Sidebar ▸ Attendance      (mark, view, export daily/monthly reports)
• Exams           → Sidebar ▸ Exams           (schedule, evaluate, publish results)
• Assignments     → Sidebar ▸ Assignments     (create, grade, track submissions)
• Fee Management  → Sidebar ▸ Fees            (fee structures, receipts, due reports)
• Communication   → Sidebar ▸ Notices         (announcements, SMS, parent messages)
• Timetable       → Sidebar ▸ Timetable       (class schedules, room allocation)
• Syllabus        → Sidebar ▸ Academic        (curriculum progress tracking)
• Library         → Sidebar ▸ Library         (book inventory, issue/return)
• HR & Payroll    → Sidebar ▸ Staff           (staff profiles, leaves, salary)
• Transport       → Sidebar ▸ Transport       (bus routes, student assignment)
• Hostel          → Sidebar ▸ Hostel          (room allocation, warden tools)
• Reports         → Sidebar ▸ Reports         (analytics, KPI dashboards)
• Admissions      → Sidebar ▸ Admissions      (enquiry pipeline, enrollment)
• Tenants         → Sidebar ▸ Tenants         (SuperAdmin only — institution management)
• Profile         → Sidebar ▸ My Profile      (personal info, password, 2FA)
• Ask Daisy       → Sidebar ▸ ✨ Ask Daisy   (you are here!)
"""

# ── Role-specific capability summaries for richer guidance ──────────────────
ROLE_GUIDANCE = {
    "Super Admin": """
You have FULL PLATFORM ACCESS across all tenants.
Key capabilities: create/manage tenants, impersonate tenant admins, view system health,
rotate API keys, access audit logs, manage all users globally.
""",
    "Institution Owner": """
You oversee the ENTIRE INSTITUTION strategically.
Key capabilities: view revenue dashboards, compare campus performance,
access board-level reports, approve major decisions, view staff across campuses.
You DO NOT manage day-to-day operations directly.
""",
    "Institutional Admin": """
You manage DAILY CAMPUS OPERATIONS.
Key capabilities: admit students, manage staff, collect fees, send notices,
approve leaves, generate reports, manage admissions pipeline.
""",
    "Institutional Leader": """
You oversee ACADEMIC QUALITY as Principal/Leader.
Key capabilities: monitor class performance, schedule/publish exams, manage
faculty, track syllabus coverage, view attendance alerts, handle academic events.
""",
    "Teacher": """
You manage YOUR CLASSES & STUDENTS.
Key capabilities: mark attendance, create/grade assignments, evaluate exams,
communicate with students and parents, view syllabus progress.
""",
    "Student": """
You access YOUR OWN ACADEMIC DATA.
Key capabilities: view timetable, submit assignments, check results,
view attendance, access library, read announcements, check fee status.
""",
    "Parent": """
You monitor YOUR CHILD'S academic journey.
Key capabilities: view attendance, check results, track assignments,
receive announcements, pay fees, message teachers.
""",
}


class DaisyService:
    """
    Core Daisy service.
    Builds a role-aware, permission-scoped system prompt and calls
    Groq's Llama 3 70B for NLP-powered responses.
    """

    def __init__(self) -> None:
        if settings.GROQ_API_KEY:
            self._client: Optional[AsyncGroq] = AsyncGroq(api_key=settings.GROQ_API_KEY)
        else:
            self._client = None
            log.warning("GROQ_API_KEY not set — Daisy will run in demo mode.")

    # ── Public API ───────────────────────────────────────────────────────────

    async def chat(
        self,
        ctx: DaisyContext,
        message: str,
        history: list[ChatHistoryItem],
    ) -> tuple[str, str]:
        """
        Returns (reply_text, intent_label).
        intent_label: navigation | permission_check | how_to | general | unknown
        """
        if not self._client:
            return self._demo_reply(ctx, message), "general"

        system_prompt = self._build_system_prompt(ctx)

        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # Inject conversation history (last 10 turns to respect token budget)
        for turn in history[-10:]:
            messages.append({"role": turn.role, "content": turn.content})

        # Current user message
        messages.append({"role": "user", "content": message})

        try:
            response = await self._client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                max_tokens=1200,
                temperature=0.65,
                top_p=0.9,
            )
            reply = response.choices[0].message.content or "I'm not sure how to help with that."

            # Lightweight intent classification (second micro-call, fast)
            intent = await self._classify_intent(message)

        except Exception as exc:
            log.error("Groq API error: %s", exc)
            reply = (
                "I'm having a little trouble connecting right now 🔌 "
                "Please check that the server is running and try again."
            )
            intent = "unknown"

        return reply, intent

    # ── System prompt builder ─────────────────────────────────────────────────

    def _build_system_prompt(self, ctx: DaisyContext) -> str:
        role_str = (
            "Super Admin (full platform access)"
            if ctx.is_super_admin
            else (", ".join(ctx.roles) if ctx.roles else "Unassigned")
        )

        # Permission block — first 40 permissions to keep prompt size sane
        if ctx.is_super_admin:
            perm_block = "  • ALL permissions (Super Admin override)"
        elif ctx.permissions:
            perm_block = "\n".join(
                f"  • {p}" for p in sorted(ctx.permissions)[:40]
            )
            if len(ctx.permissions) > 40:
                perm_block += f"\n  • …and {len(ctx.permissions) - 40} more"
        else:
            perm_block = "  • No explicit permissions assigned"

        # Role-specific capability hint
        primary_role = ctx.roles[0] if ctx.roles else "Unknown"
        role_hint = ROLE_GUIDANCE.get(
            primary_role,
            ROLE_GUIDANCE.get("Super Admin" if ctx.is_super_admin else "Unknown", "")
        )

        return f"""You are Daisy 🌼, the intelligent virtual assistant embedded inside EdVentura — a premium multi-campus educational management platform used by schools and institutions across India.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENT USER CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name           : {ctx.full_name or "User"}
Role(s)        : {role_str}
Tenant / Campus: {ctx.tenant_id or "System"}
Is Super Admin : {"YES — unrestricted access" if ctx.is_super_admin else "No"}

What this user CAN do (their permissions):
{perm_block}

Role capabilities summary:
{role_hint}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLATFORM KNOWLEDGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{EDVENTURA_MODULES}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PERSONALITY & RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. LANGUAGE: Detect the language the user writes in and ALWAYS respond in that language.
   • English  → respond in English
   • Hindi    → respond in Hindi (Devanagari or Roman — match what they used)
   • Hinglish → respond in warm, friendly Hinglish

2. PERMISSIONS: If a user asks to do something they lack permission for:
   • Tell them clearly but kindly what they cannot do
   • Explain WHO can help them (e.g., "Apne Admin se request karo")
   • Suggest an alternative if one exists

3. NAVIGATION: When guiding users, always mention the exact sidebar location:
   e.g., "Sidebar ▸ Students ▸ Add Student button pe click karo"

4. TONE: Warm, professional, concise. Not robotic. Use 1–2 relevant emojis per reply.
   For students: slightly more casual and encouraging.
   For admins/leaders: crisper and more data-focused.

5. FORMAT: Use bullet points or numbered steps for procedures. Keep replies under 200 words unless a detailed how-to is needed.

6. HONESTY: If you don't know something about the platform, say so honestly and suggest they contact support.

7. DO NOT make up permission codes, feature names, or API endpoints. Stick to what you know.

You are Daisy — not just a chatbot, but a knowledgeable colleague who genuinely wants to help."""

    # ── Intent classification (micro-call) ───────────────────────────────────

    async def _classify_intent(self, message: str) -> str:
        """Quick single-shot classification — cheap, fast."""
        if not self._client:
            return "general"
        try:
            prompt = (
                "Classify this message into ONE of: navigation, permission_check, how_to, general.\n"
                "Reply with ONLY the single word label.\n"
                f"Message: {message[:200]}"
            )
            resp = await self._client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0,
            )
            raw = (resp.choices[0].message.content or "general").strip().lower()
            return raw if raw in {"navigation", "permission_check", "how_to", "general"} else "general"
        except Exception:
            return "general"

    # ── Demo mode (no API key) ────────────────────────────────────────────────

    def _demo_reply(self, ctx: DaisyContext, message: str) -> str:
        name = ctx.full_name.split()[0] if ctx.full_name else "there"
        return (
            f"Hi {name}! 🌼 I'm Daisy, your EdVentura guide.\n\n"
            "I'm currently running in demo mode because the GROQ_API_KEY isn't configured. "
            "To enable full AI responses, please add your Groq API key to the `.env` file:\n\n"
            "  GROQ_API_KEY=gsk_your_key_here\n\n"
            "You can get a free key at https://console.groq.com"
        )


# Singleton — imported by the router
daisy_service = DaisyService()