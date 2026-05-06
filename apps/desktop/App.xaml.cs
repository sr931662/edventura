
// ════════════════════════════════════════════════════════════════════════════
// FULL App.xaml.cs for reference (copy-paste ready):
// ════════════════════════════════════════════════════════════════════════════


using EdVentura.Desktop.Infrastructure;
using edventura_desktop.Services;
using edventura_desktop.Services.Interfaces;
using edventura_desktop.ViewModels;
using edventura_desktop.ViewModels.Dialogs;
using edventura_desktop.Views;
using edventura_desktop.Views.Shell;
using Microsoft.Extensions.DependencyInjection;
using System.Windows;

namespace edventura_desktop
{
    public partial class App : Application
    {
        public static IServiceProvider ServiceProvider { get; private set; } = null!;

        protected override void OnStartup(StartupEventArgs e)
        {
            var services = new ServiceCollection();
            ConfigureServices(services);
            ServiceProvider = services.BuildServiceProvider();

            var login = ServiceProvider.GetRequiredService<LoginWindow>();
            login.Show();
        }

        private void ConfigureServices(IServiceCollection services)
        {
            // Infrastructure
            services.AddSingleton<TokenStorage>();
            services.AddSingleton<UserContext>();

            // Core services
            services.AddSingleton<ProtectionService>();
            services.AddSingleton<ThemeService>();
            services.AddSingleton<ConnectivityService>();
            services.AddSingleton<IAuthService, AuthService>();
            services.AddSingleton<AuthService>(sp => (AuthService)sp.GetRequiredService<IAuthService>());

            services.AddSingleton<INavigationService, NavigationService>();
            services.AddSingleton<IMenuService, MenuService>();

            // HTTP client
            services.AddHttpClient("Backend", client =>
            {
                client.BaseAddress = new System.Uri("http://localhost:8000/api/v1/");
                client.DefaultRequestHeaders.Accept.Add(
                    new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));
            }).AddHttpMessageHandler<AuthDelegatingHandler>();

            services.AddTransient<AuthDelegatingHandler>();
            services.AddSingleton<ApiClient>();

            services.AddTransient<IStudentService, StudentService>();

            // ── AI Assistant (Daisy) ──────────────────────────────────────
            services.AddSingleton<IDaisyService, DaisyService>();
            services.AddSingleton<DaisyViewModel>();       // singleton = chat history persists
            services.AddTransient<Views.Daisy.DaisyPanel>();

            // ViewModels
            services.AddTransient<LoginViewModel>();
            services.AddTransient<ShellViewModel>();
            services.AddTransient<StudentListViewModel>();
            services.AddTransient<ProfileViewModel>();
            services.AddTransient<StudentDialogViewModel>();
            services.AddSingleton<IDashboardService, DashboardService>();
            services.AddTransient<DashboardViewModel>();

            // Views
            services.AddTransient<LoginWindow>();
            services.AddTransient<ShellWindow>();
            services.AddTransient<DashboardPage>();
            services.AddTransient<StudentListPage>();
            services.AddTransient<ProfilePage>();
            services.AddTransient<Views.Dialogs.StudentDialog>();
        }
    }
}
