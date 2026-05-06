using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Models;
using edventura_desktop.Services;
using edventura_desktop.Services.Interfaces;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.ViewModels
{
    public partial class DashboardViewModel : ObservableObject
    {
        private readonly IDashboardService _dashboardService;

        // ── Header ────────────────────────────────────────────────────────────
        [ObservableProperty] private string _greetingPrefix = "Good morning";
        [ObservableProperty] private string _greetingName = "there";
        [ObservableProperty] private string _welcomeSubtext = "Here's what's happening today.";
        [ObservableProperty] private string _roleBadge = "User";
        [ObservableProperty] private string _todayDate = DateTime.Now.ToString("dddd, d MMMM yyyy");

        // ── State ─────────────────────────────────────────────────────────────
        [ObservableProperty] private bool _isLoading;

        // ── Legacy (kept for API compatibility) ───────────────────────────────
        [ObservableProperty] private int _totalStudents;
        [ObservableProperty] private int _totalTeachers;
        [ObservableProperty] private int _todayPresent;
        [ObservableProperty] private int _todayAbsent;

        // ── Collections ───────────────────────────────────────────────────────
        [ObservableProperty] private ObservableCollection<StatCard> _statCards = new();
        [ObservableProperty] private ObservableCollection<ActivityItem> _activities = new();
        [ObservableProperty] private ObservableCollection<QuickAction> _quickActions = new();
        [ObservableProperty] private ObservableCollection<ScheduleItem> _schedule = new();

        // ── Role visibility flags ─────────────────────────────────────────────
        public bool IsStudent => Theme?.CurrentRole == AppRole.Student;
        public bool IsSuperAdmin => Theme?.CurrentRole == AppRole.SuperAdmin;
        public bool IsOwner => Theme?.CurrentRole == AppRole.InstitutionOwner;
        public bool IsAdmin => Theme?.CurrentRole == AppRole.InstitutionAdmin;
        public bool IsLeader => Theme?.CurrentRole == AppRole.InstitutionLeader;

        private ThemeService? Theme
            => App.ServiceProvider.GetService<ThemeService>();

        public DashboardViewModel(IDashboardService dashboardService)
        {
            _dashboardService = dashboardService;
        }

        [RelayCommand]
        private async Task LoadDataAsync()
        {
            IsLoading = true;
            try
            {
                // ── Greeting ───────────────────────────────────────────────
                GreetingPrefix = GetGreetingPrefix();
                TodayDate = DateTime.Now.ToString("dddd, d MMMM yyyy");

                var user = UserSession.Instance.CurrentUser;
                GreetingName = user?.full_name?.Split(' ')[0] ?? "there";

                var role = Theme?.CurrentRole ?? AppRole.Default;
                RoleBadge = Theme?.Current.BadgeLabel ?? "User";

                // ── Legacy dashboard data ─────────────────────────────────
                var data = await _dashboardService.GetSummaryAsync();
                TotalStudents = data.TotalStudents;
                TotalTeachers = data.TotalTeachers;
                TodayPresent = data.TodayPresent;
                TodayAbsent = data.TodayAbsent;

                // ── Role-specific UI data ─────────────────────────────────
                PopulateRoleData(role);

                // notify visibility flags
                OnPropertyChanged(nameof(IsSuperAdmin));
                OnPropertyChanged(nameof(IsOwner));
                OnPropertyChanged(nameof(IsAdmin));
                OnPropertyChanged(nameof(IsLeader));
                OnPropertyChanged(nameof(IsStudent));
            }
            finally { IsLoading = false; }
        }

        // ─────────────────────────────────────────────────────────────────────
        private void PopulateRoleData(AppRole role)
        {
            StatCards.Clear();
            Activities.Clear();
            QuickActions.Clear();
            Schedule.Clear();

            switch (role)
            {
                case AppRole.SuperAdmin: LoadSuperAdminData(); break;
                case AppRole.InstitutionOwner: LoadOwnerData(); break;
                case AppRole.InstitutionAdmin: LoadAdminData(); break;
                case AppRole.InstitutionLeader: LoadLeaderData(); break;
                case AppRole.Student: LoadStudentData(); break;
                default: LoadAdminData(); break;
            }
        }

        // ── SuperAdmin ────────────────────────────────────────────────────────
        private void LoadSuperAdminData()
        {
            WelcomeSubtext = "Platform-wide health, tenants and system operations.";

            S("🏫", "Active Tenants", "8", "↑ 2 this month", true, "#EFF6FF", "#3B82F6");
            S("👥", "Total Users", "1,247", "↑ 38 this week", true, "#F0FDF4", "#059669");
            S("⚡", "System Uptime", "99.8%", "↓ 0.01% variance", false, "#FFFBEB", "#D97706");
            S("🔔", "Active Alerts", "3", "1 critical", false, "#FEF2F2", "#EF4444");

            A("#3B82F6", "🏫", "New Tenant Onboarded", "DPS North Campus registered", "2 min ago");
            A("#059669", "✅", "System Backup Complete", "All 8 tenant DBs backed up", "18 min ago");
            A("#D97706", "⚠️", "High Memory Alert", "Server 02 — 87% memory", "34 min ago");
            A("#6366F1", "🔑", "API Key Rotated", "Tenant: RLB School, key refreshed", "1 hr ago");
            A("#EF4444", "🛡️", "Failed Login Attempt", "IP: 192.168.1.44 blocked", "2 hr ago");

            Q("🏫", "Add Tenant", "#EFF6FF", "#3B82F6");
            Q("👥", "Manage Users", "#F0FDF4", "#059669");
            Q("⚙️", "System Config", "#FFFBEB", "#D97706");
            Q("📋", "Audit Logs", "#FEF2F2", "#EF4444");
        }

        // ── Institution Owner ─────────────────────────────────────────────────
        private void LoadOwnerData()
        {
            WelcomeSubtext = "Strategic oversight of your institution network.";

            S("🏫", "Campuses", "3", "All operational", true, "#EEF2FF", "#6366F1");
            S("💰", "Monthly Revenue", "₹48.2L", "↑ 12% vs last mo", true, "#F0FDF4", "#059669");
            S("🎓", "Total Enrolled", "1,247", "↑ 89 this term", true, "#EEF2FF", "#6366F1");
            S("👨‍🏫", "Staff Count", "186", "3 positions open", false, "#FFFBEB", "#D97706");

            A("#6366F1", "💰", "Fee Collection Update", "Campus A collected ₹8.4L today", "5 min ago");
            A("#059669", "📈", "Enrollment Milestone", "Batch 2025 crosses 400 students", "1 hr ago");
            A("#D97706", "📋", "Board Report Ready", "Q1 2025 report generated", "3 hr ago");
            A("#8B5CF6", "🏗️", "Campus C Renovation", "Phase 2 approved, starts May 15", "Yesterday");
            A("#059669", "⭐", "CBSE Accreditation", "Campus A re-accredited A+ grade", "2 days ago");

            Q("📊", "Financial Report", "#EEF2FF", "#6366F1");
            Q("🏫", "Add Campus", "#F0FDF4", "#059669");
            Q("👥", "View All Staff", "#FFFBEB", "#D97706");
            Q("📋", "Strategic Plan", "#FDF4FF", "#8B5CF6");
        }

        // ── Institutional Admin ───────────────────────────────────────────────
        private void LoadAdminData()
        {
            WelcomeSubtext = "Campus operations at a glance.";

            S("🎓", "Total Students", "842", "↑ 12 this week", true, "#ECFDF5", "#059669");
            S("👨‍🏫", "Staff Present", "43 / 48", "5 on leave", false, "#F0FDF4", "#0D9488");
            S("💰", "Fees Collected", "₹12.4L", "↑ 8% this month", true, "#ECFDF5", "#059669");
            S("📋", "Pending Leaves", "7", "↑ 3 new today", false, "#FFFBEB", "#D97706");

            A("#059669", "✅", "New Admission", "Aryan Sharma, Class 9A admitted", "10 min ago");
            A("#0D9488", "📋", "Leave Approved", "Ms. Priya Nair — 2 day leave", "25 min ago");
            A("#D97706", "⚠️", "Fee Reminder Sent", "45 students with pending dues", "1 hr ago");
            A("#6366F1", "📢", "Notice Circulated", "Sports Day — May 12, all classes", "2 hr ago");
            A("#059669", "🎓", "Admission Inquiry", "12 new inquiries via website", "3 hr ago");

            Q("➕", "Add Student", "#ECFDF5", "#059669");
            Q("👨‍🏫", "Staff Mgmt", "#F0FDF4", "#0D9488");
            Q("💰", "Fee Reports", "#FFFBEB", "#D97706");
            Q("📢", "Send Notice", "#EEF2FF", "#6366F1");
        }

        // ── Institutional Leader (Principal) ──────────────────────────────────
        private void LoadLeaderData()
        {
            WelcomeSubtext = "Academic performance and faculty overview.";

            S("⭐", "Academic Grade", "A+", "↑ from A last year", true, "#FFFBEB", "#D97706");
            S("📊", "Avg Score", "78.4%", "↑ 3.2% this term", true, "#FFFBEB", "#B45309");
            S("📅", "Events / Month", "5", "Next: Sports Day", true, "#ECFDF5", "#059669");
            S("👨‍🏫", "Faculty Rating", "92%", "↑ 4% this quarter", true, "#FFFBEB", "#D97706");

            A("#D97706", "📊", "Class 10A Results", "Avg: 81.2% — Top class this term", "30 min ago");
            A("#059669", "✅", "Syllabus Coverage", "Class 11 Physics — 94% on track", "1 hr ago");
            A("#B45309", "📋", "Faculty Appraisal Due", "7 teachers pending review", "2 hr ago");
            A("#6366F1", "🏆", "Olympiad Results", "3 students qualify for state round", "Yesterday");
            A("#EF4444", "⚠️", "Low Attendance Alert", "Class 8B — below 75%", "Yesterday");

            Q("📊", "View Results", "#FFFBEB", "#D97706");
            Q("📝", "Schedule Exam", "#ECFDF5", "#059669");
            Q("👨‍🏫", "Faculty Review", "#FDF4FF", "#8B5CF6");
            Q("📅", "Academic Cal.", "#EEF2FF", "#6366F1");
        }

        // ── Student ───────────────────────────────────────────────────────────
        private void LoadStudentData()
        {
            WelcomeSubtext = "Your academic snapshot for today.";

            S("📅", "Attendance", "88%", "↑ 2% this month", true, "#F5F3FF", "#7C3AED");
            S("🎯", "CGPA", "8.4", "↑ 0.2 this sem", true, "#FDF2F8", "#DB2777");
            S("📝", "Pending Tasks", "3", "Due within 3 days", false, "#FFF7ED", "#EA580C");
            S("📚", "Upcoming Exams", "2", "Next: Maths, May 8", false, "#F5F3FF", "#7C3AED");

            A("#7C3AED", "📝", "Assignment Graded", "Physics Lab — 18/20 ✨", "1 hr ago");
            A("#DB2777", "📢", "Announcement", "Mid-term schedule now posted", "2 hr ago");
            A("#059669", "✅", "Attendance Marked", "All 6 periods attended today", "3 hr ago");
            A("#D97706", "⚠️", "Assignment Reminder", "Math worksheet due tomorrow", "Yesterday");
            A("#6366F1", "🏆", "Achievement Unlocked", "Perfect attendance — March 2025", "2 days ago");

            Q("📝", "Assignments", "#F5F3FF", "#7C3AED");
            Q("📊", "My Results", "#FDF2F8", "#DB2777");
            Q("📚", "Library", "#ECFDF5", "#059669");
            Q("💰", "Fee Status", "#FFFBEB", "#D97706");

            Schedule.Add(new() { Time = "08:00", Subject = "Mathematics", Room = "Room 12", IsNow = false });
            Schedule.Add(new() { Time = "09:00", Subject = "Physics", Room = "Lab 02", IsNow = true });
            Schedule.Add(new() { Time = "10:00", Subject = "English Lit.", Room = "Room 07", IsNow = false });
            Schedule.Add(new() { Time = "11:00", Subject = "Chemistry", Room = "Lab 01", IsNow = false });
            Schedule.Add(new() { Time = "12:00", Subject = "Lunch Break", Room = "Canteen", IsNow = false, IsFree = true });
            Schedule.Add(new() { Time = "13:00", Subject = "Computer Sci.", Room = "Comp. Lab", IsNow = false });
            Schedule.Add(new() { Time = "14:00", Subject = "Physical Edu.", Room = "Ground", IsNow = false });
        }

        // ── Helpers ───────────────────────────────────────────────────────────
        private void S(string icon, string label, string value, string trend, bool isUp, string iconBg, string iconColor)
            => StatCards.Add(new() { Icon = icon, Label = label, Value = value, Trend = trend, IsUp = isUp, IconBg = iconBg, IconColor = iconColor });

        private void A(string dotColor, string icon, string title, string desc, string time)
            => Activities.Add(new() { DotColor = dotColor, Icon = icon, Title = title, Description = desc, TimeAgo = time });

        private void Q(string icon, string label, string bg, string fg)
            => QuickActions.Add(new() { Icon = icon, Label = label, Bg = bg, Fg = fg });

        private static string GetGreetingPrefix()
        {
            int h = DateTime.Now.Hour;
            return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
        }
    }
}