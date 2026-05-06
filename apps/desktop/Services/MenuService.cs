using System;
using System.Collections.Generic;
using edventura_desktop.Services.Interfaces;
using edventura_desktop.Views;
using edventura_desktop.Views.Shell;

namespace edventura_desktop.Services
{
    public class MenuService : IMenuService
    {
        private readonly ThemeService _themeService;

        public MenuService(ThemeService themeService) => _themeService = themeService;

        public IEnumerable<MenuItem> GetMenuItems()
        {
            var role = _themeService.CurrentRole;
            var items = new List<MenuItem>();

            // ── Dashboard (all roles) ──────────────────────────────────────
            items.Add(new() { Title = "Dashboard", Icon = "📊", PageType = typeof(DashboardPage) });

            // ── SuperAdmin ─────────────────────────────────────────────────
            if (role == AppRole.SuperAdmin)
            {
                items.Add(new() { Title = "Tenants", Icon = "🏫", PageType = typeof(DashboardPage) });
                items.Add(new() { Title = "All Users", Icon = "👥", PageType = typeof(DashboardPage) });
                items.Add(new() { Title = "System Config", Icon = "⚙️", PageType = typeof(DashboardPage) });
                items.Add(new() { Title = "Audit Logs", Icon = "📋", PageType = typeof(DashboardPage) });
            }

            // ── Institution Owner ──────────────────────────────────────────
            if (role == AppRole.InstitutionOwner)
            {
                items.Add(new() { Title = "Campuses", Icon = "🏫", PageType = typeof(DashboardPage) });
                items.Add(new() { Title = "Financials", Icon = "💰", PageType = typeof(DashboardPage) });
                items.Add(new() { Title = "Reports", Icon = "📈", PageType = typeof(DashboardPage) });
                items.Add(new() { Title = "Staff", Icon = "👨‍🏫", PageType = typeof(DashboardPage) });
            }

            // ── Institutional Admin ────────────────────────────────────────
            if (role == AppRole.InstitutionAdmin)
            {
                items.Add(new()
                {
                    Title = "Students",
                    Icon = "🎓",
                    PageType = typeof(StudentListPage),
                    PermissionRequired = "student:read"
                });
                items.Add(new() { Title = "Staff", Icon = "👨‍🏫", PageType = typeof(DashboardPage) });
                items.Add(new()
                {
                    Title = "Admissions",
                    Icon = "📋",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "admission:read"
                });
                items.Add(new()
                {
                    Title = "Fees",
                    Icon = "💰",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "fee:read"
                });
                items.Add(new() { Title = "Notices", Icon = "📢", PageType = typeof(DashboardPage) });
            }

            // ── Institutional Leader (Principal) ───────────────────────────
            if (role == AppRole.InstitutionLeader)
            {
                items.Add(new() { Title = "Academic", Icon = "📚", PageType = typeof(DashboardPage) });
                items.Add(new()
                {
                    Title = "Exams",
                    Icon = "📝",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "exam:read"
                });
                items.Add(new() { Title = "Faculty", Icon = "👨‍🏫", PageType = typeof(DashboardPage) });
                items.Add(new()
                {
                    Title = "Timetable",
                    Icon = "📅",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "timetable:read"
                });
            }

            // ── Student ────────────────────────────────────────────────────
            if (role == AppRole.Student)
            {
                items.Add(new() { Title = "My Classes", Icon = "📚", PageType = typeof(DashboardPage) });
                items.Add(new()
                {
                    Title = "Assignments",
                    Icon = "📝",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "assignment:read"
                });
                items.Add(new()
                {
                    Title = "Results",
                    Icon = "📊",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "exam:read"
                });
                items.Add(new()
                {
                    Title = "Attendance",
                    Icon = "📅",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "attendance:read"
                });
                items.Add(new()
                {
                    Title = "Library",
                    Icon = "📖",
                    PageType = typeof(DashboardPage),
                    PermissionRequired = "library:read"
                });
            }

            // ── Profile (all roles) ────────────────────────────────────────
            items.Add(new() { Title = "My Profile", Icon = "👤", PageType = typeof(ProfilePage) });

            return items;
        }
    }
}