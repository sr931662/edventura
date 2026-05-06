using System.Collections.Generic;
using System.Windows;
using System.Windows.Media;
using edventura_desktop.Models;

namespace edventura_desktop.Services
{
    public class ThemeService
    {
        private readonly Dictionary<string, string> _roleColors = new()
        {
            ["Super Admin"] = "#0F172A",         // default core
            ["Institution Owner"] = "#1E3A8A",
            ["Institution Leader"] = "#4338CA",
            ["Institution Admin"] = "#475569",
            ["Sub-Admin"] = "#64748B",
            ["Registrar"] = "#0F766E",
            ["Accountant"] = "#059669",
            ["Finance Head"] = "#047857",
            ["HOD"] = "#6D28D9",
            ["Teacher"] = "#3B82F6",
            ["Student"] = "#06B6D4",
            ["Parent"] = "#D97706",
            ["Librarian"] = "#92400E",
            ["Exam Controller"] = "#B91C1C",
            ["Admission Counsellor"] = "#0284C7",
            ["Academic Coordinator"] = "#2563EB",
            ["Class Teacher"] = "#60A5FA",
            ["Transport Manager"] = "#CA8A04",
            ["Hostel Manager"] = "#4D7C0F",
            ["HR Manager"] = "#DB2777",
            ["IT Head"] = "#0891B2",
            ["Counsellor"] = "#8B5CF6",
            ["Medical Staff"] = "#16A34A",
            ["Activity Coordinator"] = "#F97316",
            ["Sports Coach"] = "#EA580C",
            ["Vendor"] = "#525252"
        };

        public Color? GetAccentColor(UserProfile user)
        {
            if (user.is_super_admin)
                return (Color)ColorConverter.ConvertFromString("#0F172A");

            var roles = user.roles ?? new List<string>();
            // highest precedence: order as in list; pick first match
            foreach (var role in _roleColors.Keys)
                if (roles.Contains(role))
                    return (Color)ColorConverter.ConvertFromString(_roleColors[role]);

            return (Color)ColorConverter.ConvertFromString("#3B82F6"); // default blue
        }
    }
}