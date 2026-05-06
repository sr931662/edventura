using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Media;
using edventura_desktop.Models;
using edventura_desktop.Services;

namespace edventura_desktop
{
    public enum AppRole
    {
        SuperAdmin,
        InstitutionOwner,
        InstitutionAdmin,
        InstitutionLeader,
        Student,
        Default
    }

    public class RoleTheme
    {
        public string Primary { get; init; } = "#3B82F6";
        public string Secondary { get; init; } = "#06B6D4";
        public string Light { get; init; } = "#EFF6FF";
        public string SidebarTop { get; init; } = "#0A1628";
        public string SidebarBot { get; init; } = "#0F2040";
        public string BadgeLabel { get; init; } = "User";
    }

    public class ThemeService
    {
        public static readonly Dictionary<AppRole, RoleTheme> Themes = new()
        {
            [AppRole.SuperAdmin] = new()
            {
                Primary = "#3B82F6",
                Secondary = "#06B6D4",
                Light = "#EFF6FF",
                SidebarTop = "#0A1628",
                SidebarBot = "#0F2040",
                BadgeLabel = "System Admin"
            },
            [AppRole.InstitutionOwner] = new()
            {
                Primary = "#6366F1",
                Secondary = "#8B5CF6",
                Light = "#EEF2FF",
                SidebarTop = "#1E1B4B",
                SidebarBot = "#312E81",
                BadgeLabel = "Owner"
            },
            [AppRole.InstitutionAdmin] = new()
            {
                Primary = "#059669",
                Secondary = "#0D9488",
                Light = "#ECFDF5",
                SidebarTop = "#022C22",
                SidebarBot = "#064E3B",
                BadgeLabel = "Admin"
            },
            [AppRole.InstitutionLeader] = new()
            {
                Primary = "#D97706",
                Secondary = "#B45309",
                Light = "#FFFBEB",
                SidebarTop = "#1C0A00",
                SidebarBot = "#451A03",
                BadgeLabel = "Principal"
            },
            [AppRole.Student] = new()
            {
                Primary = "#7C3AED",
                Secondary = "#DB2777",
                Light = "#F5F3FF",
                SidebarTop = "#1E0A3C",
                SidebarBot = "#2D1B69",
                BadgeLabel = "Student"
            },
        };

        public AppRole CurrentRole { get; private set; } = AppRole.Default;
        public RoleTheme Current => Themes.GetValueOrDefault(CurrentRole, Themes[AppRole.SuperAdmin]);

        public void ApplyFromProfile(UserProfile profile)
        {
            Apply(DetectRole(profile.is_super_admin, profile.roles));
        }

        public void ApplyFromUserSession()
        {
            var user = UserSession.Instance.CurrentUser;
            if (user != null) ApplyFromProfile(user);
        }

        private static AppRole DetectRole(bool isSuperAdmin, List<string>? roles)
        {
            if (isSuperAdmin) return AppRole.SuperAdmin;
            if (roles == null || roles.Count == 0) return AppRole.Default;

            if (roles.Exists(r => r.Contains("Owner", StringComparison.OrdinalIgnoreCase))) return AppRole.InstitutionOwner;
            if (roles.Exists(r => r.Contains("Admin", StringComparison.OrdinalIgnoreCase))) return AppRole.InstitutionAdmin;
            if (roles.Exists(r => r.Contains("Leader", StringComparison.OrdinalIgnoreCase)
                               || r.Contains("Principal", StringComparison.OrdinalIgnoreCase))) return AppRole.InstitutionLeader;
            if (roles.Exists(r => r.Contains("Student", StringComparison.OrdinalIgnoreCase))) return AppRole.Student;

            return AppRole.Default;
        }

        public void Apply(AppRole role)
        {
            CurrentRole = role;
            var t = Themes.GetValueOrDefault(role, Themes[AppRole.SuperAdmin]);
            var res = Application.Current.Resources;

            // Sidebar gradient (vertical dark-to-darker)
            var sidebar = new LinearGradientBrush
            {
                StartPoint = new Point(0, 0),
                EndPoint = new Point(0, 1)
            };
            sidebar.GradientStops.Add(new GradientStop(H(t.SidebarTop), 0));
            sidebar.GradientStops.Add(new GradientStop(H(t.SidebarBot), 1));
            res["SidebarGradient"] = sidebar;

            // Button gradient (horizontal secondary→primary)
            var btn = new LinearGradientBrush
            {
                StartPoint = new Point(0, 0),
                EndPoint = new Point(1, 0)
            };
            btn.GradientStops.Add(new GradientStop(H(t.Secondary), 0));
            btn.GradientStops.Add(new GradientStop(H(t.Primary), 1));
            res["ButtonGradient"] = btn;

            // Solid brushes (DynamicResource targets in XAML)
            res["AccentPrimary"] = new SolidColorBrush(H(t.Primary));
            res["AccentSecondary"] = new SolidColorBrush(H(t.Secondary));
            res["AccentLight"] = new SolidColorBrush(H(t.Light));

            // Raw Color values (for ColorAnimation)
            res["AccentPrimaryColor"] = H(t.Primary);
            res["AccentSecondaryColor"] = H(t.Secondary);
        }

        private static Color H(string hex)
        {
            hex = hex.TrimStart('#');
            return Color.FromRgb(
                Convert.ToByte(hex[..2], 16),
                Convert.ToByte(hex[2..4], 16),
                Convert.ToByte(hex[4..6], 16));
        }
    }
}