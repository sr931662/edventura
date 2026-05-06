using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using edventura_desktop.Services;
using edventura_desktop.ViewModels;
using edventura_desktop.Views;

namespace edventura_desktop
{
    public partial class App : Application
    {
        public static IServiceProvider ServiceProvider { get; private set; } = default!;

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
            // Core services
            services.AddSingleton<ProtectionService>();
            services.AddSingleton<ThemeService>();
            services.AddSingleton<ConnectivityService>();
            services.AddSingleton<AuthService>();

            // HttpClient factory with token‑refresh delegating handler
            services.AddHttpClient("Backend", client =>
            {
                client.BaseAddress = new System.Uri("http://localhost:8000");
                client.DefaultRequestHeaders.Accept.Add(
                    new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));
            }).AddHttpMessageHandler<AuthenticationDelegatingHandler>();

            services.AddTransient<AuthenticationDelegatingHandler>();
            services.AddSingleton<ApiClient>();   // holds method helpers

            // ViewModels
            services.AddTransient<LoginViewModel>();
            services.AddSingleton<ShellViewModel>();

            // Views
            services.AddTransient<LoginWindow>();
            services.AddSingleton<ShellWindow>();
        }
    }
}