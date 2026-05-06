from .attendance_models import (
    AttendancePolicy, AttendanceRecord, TeacherClassAssignment,
    EmployeePunchLog, ShiftSchedule, AttendanceComputation,
    AttendanceRecoverySession, Device, BiometricTemplate,
    QRCheckinLog, BLENFCLog, TransportAttendance, HostelMovement,
    EmployeeLeave, AdvancedAttendanceAnalytics,
    ComplianceDocument, AttendanceAuditLog, TenantBranding,
    ConsolidatedAttendance
)

from .gamification_models import (
    GamificationStreak, GamificationPoints, GamificationBadge,
    GamificationInventory, GamificationRedemption,
    GamificationTournament, GamificationTournamentScore,
    GamificationSocialFeed, OnlineSessionLog, RiskScore,
    ForecastModel, VoiceCommandLog,
)
from .finance_models import *   # or list all classes