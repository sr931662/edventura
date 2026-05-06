using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;

namespace edventura_desktop.ViewModels
{
    public partial class UsersViewModel : ObservableObject
    {
        private readonly AdminService _adminService;

        [ObservableProperty]
        private ObservableCollection<UserAdminDto>? users;

        [ObservableProperty]
        private string newEmail = "";

        [ObservableProperty]
        private string newPassword = "Test@2026";

        [ObservableProperty]
        private string newFullName = "";

        [ObservableProperty]
        private string selectedRoleName = "Teacher";

        public ObservableCollection<RoleDto> Roles { get; } = new();

        public UsersViewModel(AdminService adminService)
        {
            _adminService = adminService;
            _ = LoadAsync();
        }

        [RelayCommand]
        private async Task LoadAsync()
        {
            var users = await _adminService.GetUsersAsync();
            Users = new ObservableCollection<UserAdminDto>(users);

            Roles.Clear();
            foreach (var r in await _adminService.GetRolesAsync())
                Roles.Add(r);
        }

        [RelayCommand]
        private async Task CreateUserAsync()
        {
            try
            {
                await _adminService.CreateUserAsync(NewEmail, NewPassword, NewFullName, SelectedRoleName);
                await LoadAsync();
            }
            catch (System.Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}");
            }
        }

        [RelayCommand]
        private async Task DeleteUserAsync(UserAdminDto user)
        {
            if (MessageBox.Show($"Delete {user.full_name}?", "Confirm", MessageBoxButton.YesNo) == MessageBoxResult.Yes)
            {
                await _adminService.DeleteUserAsync(user.id);
                await LoadAsync();
            }
        }
    }
}