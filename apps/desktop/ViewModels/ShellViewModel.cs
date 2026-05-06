using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;
using edventura_desktop.Services.Interfaces;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;   // <-- add
using System.Windows;

namespace edventura_desktop.ViewModels
{
    public partial class ShellViewModel : ObservableObject
    {
        private readonly AuthService _authService;
        private readonly INavigationService _navigationService;

        [ObservableProperty]
        private string _userName = "";

        [ObservableProperty]
        private string _userRole = "";

        public IEnumerable<MenuItem> MenuItems { get; }

        public ShellViewModel(IMenuService menuService, INavigationService navigationService, AuthService authService)
        {
            _authService = authService;
            _navigationService = navigationService;

            var user = UserSession.Instance.CurrentUser;
            if (user != null)
            {
                UserName = user.full_name;
                UserRole = user.is_super_admin ? "Super Admin" : string.Join(", ", user.roles ?? new());
            }

            MenuItems = menuService.GetMenuItems();
        }

        [RelayCommand]
        private void Navigate(Type pageType)
        {
            var method = typeof(INavigationService).GetMethod("NavigateTo")?.MakeGenericMethod(pageType);
            method?.Invoke(_navigationService, null);
        }

        [RelayCommand]
        private async Task Logout()   // now async
        {
            await _authService.LogoutAsync();
            var login = App.ServiceProvider.GetRequiredService<Views.LoginWindow>();
            login.Show();
            Application.Current.Windows[0]?.Close();
        }
    }
}