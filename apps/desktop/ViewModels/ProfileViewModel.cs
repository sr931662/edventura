using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;
using System;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;

namespace edventura_desktop.ViewModels
{
    public partial class ProfileViewModel : ObservableObject
    {
        private readonly AuthService _authService;

        // ── Profile data ──────────────────────────────────────────────────
        [ObservableProperty] private string _fullName = "";
        [ObservableProperty] private string _email = "";
        [ObservableProperty] private string _phone = "";
        [ObservableProperty] private string _roles = "";
        [ObservableProperty] private string _initials = "";
        [ObservableProperty] private string _badgeLabel = "";
        [ObservableProperty] private string _tenantInfo = "";

        // ── Permission counts ─────────────────────────────────────────────
        [ObservableProperty] private string _permissionSummary = "";
        [ObservableProperty] private int _permissionCount;

        // ── Flags ─────────────────────────────────────────────────────────
        [ObservableProperty] private bool _isSuperAdmin;
        [ObservableProperty] private bool _isLoading;

        // ── Theme accent passthrough ──────────────────────────────────────
        public string AccentHex => App.ServiceProvider
            .GetService(typeof(ThemeService)) is ThemeService ts
            ? ts.Current.Primary : "#3B82F6";

        public ProfileViewModel(AuthService authService)
        {
            _authService = authService;
        }

        [RelayCommand]
        private async Task LoadProfileAsync()
        {
            IsLoading = true;
            try
            {
                var user = UserSession.Instance.CurrentUser
                           ?? await _authService.GetUserProfileAsync();

                FullName = user.full_name;
                Email = user.email;
                Phone = user.phone ?? "Not provided";
                Roles = string.Join(" · ", user.roles ?? new());
                IsSuperAdmin = user.is_super_admin;

                // Initials (up to 2 letters)
                var parts = (user.full_name ?? "U").Split(' ', StringSplitOptions.RemoveEmptyEntries);
                Initials = parts.Length >= 2
                    ? $"{parts[0][0]}{parts[^1][0]}"
                    : (parts[0][..Math.Min(2, parts[0].Length)]);
                Initials = Initials.ToUpperInvariant();

                BadgeLabel = IsSuperAdmin ? "System Admin"
                    : user.roles?.FirstOrDefault() ?? "User";

                TenantInfo = user.tenant_id != null
                    ? $"Tenant ID  ·  {user.tenant_id[..Math.Min(8, user.tenant_id.Length)]}…"
                    : "System Tenant";

                var perms = user.permissions ?? new();
                PermissionCount = perms.Count;
                PermissionSummary = PermissionCount == 0
                    ? "All permissions (Super Admin)"
                    : $"{PermissionCount} permissions across {(Roles.Split('·').Length)} role(s)";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not load profile: {ex.Message}", "Error",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
            }
            finally { IsLoading = false; }
        }
    }
}