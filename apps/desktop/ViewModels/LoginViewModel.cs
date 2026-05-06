using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;
using System;
using System.Threading.Tasks;

namespace edventura_desktop.ViewModels
{
    public partial class LoginViewModel : ObservableObject
    {
        private readonly AuthService _authService;
        private readonly ThemeService _themeService;

        public event Action? LoginSucceeded;

        [ObservableProperty] private string _email = "owner@rlb.demo";
        [ObservableProperty] private string _password = "Test@2026";
        [ObservableProperty] private bool _isBusy;
        [ObservableProperty] private string _errorMessage = "";
        [ObservableProperty] private bool _hasError;

        public LoginViewModel(AuthService authService, ThemeService themeService)
        {
            _authService = authService;
            _themeService = themeService;
        }

        [RelayCommand]
        private async Task LoginAsync()
        {
            IsBusy = true;
            HasError = false;
            ErrorMessage = "";

            try
            {
                // 1. Authenticate — stores tokens in TokenStorage
                await _authService.LoginAsync(Email, Password);

                // 2. Fetch full profile so ShellViewModel has a name + roles
                var profile = await _authService.GetUserProfileAsync();

                // 3. Populate UserSession so ShellViewModel can read display name / role
                UserSession.Instance.SetUserProfile(profile);

                // 4. Apply role-based theme before shell opens
                _themeService.ApplyFromProfile(profile);

                LoginSucceeded?.Invoke();
            }
            catch (Exception ex)
            {
                HasError = true;
                ErrorMessage = ex.Message.Contains("401") || ex.Message.Contains("Unauthorized")
                    ? "Invalid email or password."
                    : "Could not connect. Check your network.";
            }
            finally
            {
                IsBusy = false;
            }
        }
    }
}