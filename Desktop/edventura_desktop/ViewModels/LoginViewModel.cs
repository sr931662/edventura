using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.ViewModels
{
    public partial class LoginViewModel : ObservableObject
    {
        private readonly AuthService _authService = default!;
        private readonly ThemeService _themeService = default!;

        [ObservableProperty]
        private string email = "owner@rlb.demo";
        [ObservableProperty]
        private string password = "Test@2026";
        [ObservableProperty]
        private bool isBusy;

        public LoginViewModel() { }

        public LoginViewModel(AuthService authService, ThemeService themeService)
        {
            _authService = authService;
            _themeService = themeService;
        }

        [RelayCommand]
        private async Task LoginAsync(object parameter)
        {
            try
            {
                IsBusy = true;
                await _authService.LoginAsync(Email, Password);
                // Navigate to shell
                Application.Current.Dispatcher.Invoke(() =>
                {
                    var shell = App.ServiceProvider.GetRequiredService<Views.ShellWindow>();
                    shell.Show();
                    // Close login window
                    foreach (Window window in Application.Current.Windows)
                        if (window is Views.LoginWindow)
                        {
                            window.Close();
                            break;
                        }
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Login failed: {ex.Message}", "Authentication Error",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                IsBusy = false;
            }
        }
    }
}