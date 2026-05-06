using edventura_desktop.Services;
using Microsoft.Extensions.DependencyInjection;
using System.Windows;
using System.Windows.Media;

namespace edventura_desktop.Views
{
    public partial class ShellWindow : Window
    {
        public ShellWindow()
        {
            InitializeComponent();
            var themeService = App.ServiceProvider.GetRequiredService<ThemeService>();
            var authService = App.ServiceProvider.GetRequiredService<AuthService>();
            var user = authService.CurrentUser;
            if (user != null)
            {
                var accent = themeService.GetAccentColor(user);
                if (accent.HasValue && Resources["AccentBrush"] is SolidColorBrush brush)
                    brush.Color = accent.Value;
            }
            DataContext = App.ServiceProvider.GetRequiredService<ViewModels.ShellViewModel>();
        }
    }
}