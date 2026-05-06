using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using edventura_desktop.Models;

namespace edventura_desktop.Services
{
    public class AdminService
    {
        private readonly ApiClient _api;

        public AdminService(ApiClient api) => _api = api;

        // Roles
        public async Task<List<RoleDto>> GetRolesAsync() =>
            await _api.GetAsync<List<RoleDto>>("/api/v1/admin/roles") ?? new();

        public async Task<RoleDto> CreateRoleAsync(string name, string description) =>
            await _api.PostAsJsonAsync<object, RoleDto>("/api/v1/admin/roles", new { name, description });

        public async Task UpdateRoleAsync(string roleId, string name, string description) =>
            await _api.PutAsJsonAsync($"/api/v1/admin/roles/{roleId}", new { name, description });

        public async Task DeleteRoleAsync(string roleId) =>
            await _api.DeleteAsync($"/api/v1/admin/roles/{roleId}");

        // Users
        public async Task<List<UserAdminDto>> GetUsersAsync() =>
            await _api.GetAsync<List<UserAdminDto>>("/api/v1/admin/users") ?? new();

        public async Task<UserAdminDto> CreateUserAsync(string email, string password, string fullName, string roleName) =>
            await _api.PostAsJsonAsync<object, UserAdminDto>("/api/v1/admin/users",
                new { email, password, full_name = fullName, role_name = roleName });

        public async Task UpdateUserAsync(string userId, object payload) =>
            await _api.PutAsJsonAsync($"/api/v1/admin/users/{userId}", payload);

        public async Task DeleteUserAsync(string userId) =>
            await _api.DeleteAsync($"/api/v1/admin/users/{userId}");
    }

    public class RoleDto
    {
        public string id { get; set; } = "";
        public string name { get; set; } = "";
        public string description { get; set; } = "";
        public bool is_system { get; set; }
    }

    public class UserAdminDto
    {
        public string id { get; set; } = "";
        public string email { get; set; } = "";
        public string full_name { get; set; } = "";
        public bool is_active { get; set; }
        public bool is_super_admin { get; set; }
        public List<string>? roles { get; set; }
    }
}