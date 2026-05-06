using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;
using Microsoft.Extensions.DependencyInjection;
using System.Windows;

namespace edventura_desktop.ViewModels
{
    public partial class ShellViewModel : ObservableObject
    {
        private readonly AuthService _authService = default!;
        private readonly ConnectivityService _connectivity = default!;
        private readonly ThemeService _themeService = default!;

        [ObservableProperty]
        private string statusText = "Online";

        [ObservableProperty]
        private string currentUserName = "User";

        [ObservableProperty]
        private string currentRole = "Unknown";

        public ObservableCollection<NavItem> NavigationItems { get; } = new();

        public ShellViewModel() { }   // design‑time only

        public ShellViewModel(AuthService authService, ConnectivityService connectivity, ThemeService themeService)
        {
            _authService = authService;
            _connectivity = connectivity;
            _themeService = themeService;

            // Connectivity updates
            _connectivity.ConnectivityChanged += (online) =>
                StatusText = online ? "Online" : "Offline";

            // User info
            var user = _authService.CurrentUser;
            if (user != null)
            {
                CurrentUserName = user.full_name;
                CurrentRole = user.is_super_admin
                    ? "Super Admin"
                    : string.Join(", ", user.roles ?? new());
            }

            // Navigation items (placeholders; will be dynamic based on role later)
            NavigationItems.Add(new NavItem { Title = "Home", Icon = "🏠", PageKey = "Home" });
            NavigationItems.Add(new NavItem { Title = "Users", Icon = "👤", PageKey = "Users" });
            NavigationItems.Add(new NavItem { Title = "Settings", Icon = "⚙️", PageKey = "Settings" });
        }

        [RelayCommand]
        private void Navigate(string pageKey)
        {
            // Will be connected to a navigation service in Phase 2
            MessageBox.Show($"Navigating to {pageKey} – to be implemented.");
        }

        [RelayCommand]
        public void Logout()
        {
            _authService.Logout();
            Application.Current.Dispatcher.Invoke(() =>
            {
                var login = App.ServiceProvider.GetRequiredService<Views.LoginWindow>();
                login.Show();
                foreach (Window window in Application.Current.Windows)
                    if (window is Views.ShellWindow)
                    {
                        window.Close();
                        break;
                    }
            });
        }
    }

    public class NavItem
    {
        public string Title { get; set; } = "";
        public string Icon { get; set; } = "";
        public string PageKey { get; set; } = "";
    }
}