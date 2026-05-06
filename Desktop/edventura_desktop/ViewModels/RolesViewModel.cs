using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;
using System.Collections.ObjectModel;
using System.Data;
using System.Threading.Tasks;
using System.Windows;

namespace edventura_desktop.ViewModels
{
    public partial class RolesViewModel : ObservableObject
    {
        private readonly AdminService _adminService;

        [ObservableProperty]
        private ObservableCollection<RoleDto>? roles;

        [ObservableProperty]
        private string newRoleName = "";

        [ObservableProperty]
        private string newRoleDescription = "";

        public RolesViewModel(AdminService adminService)
        {
            _adminService = adminService;
            _ = LoadAsync();
        }

        [RelayCommand]
        private async Task LoadAsync()
        {
            var roles = await _adminService.GetRolesAsync();
            Roles = new ObservableCollection<RoleDto>(roles);
        }

        [RelayCommand]
        private async Task CreateRoleAsync()
        {
            try
            {
                await _adminService.CreateRoleAsync(NewRoleName, NewRoleDescription);
                NewRoleName = "";
                NewRoleDescription = "";
                await LoadAsync();
            }
            catch (System.Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}");
            }
        }

        [RelayCommand]
        private async Task DeleteRoleAsync(RoleDto role)
        {
            if (MessageBox.Show($"Delete role {role.name}?", "Confirm", MessageBoxButton.YesNo) == MessageBoxResult.Yes)
            {
                await _adminService.DeleteRoleAsync(role.id);
                await LoadAsync();
            }
        }
    }
}