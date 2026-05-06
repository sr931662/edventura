using edventura_desktop.Models;
using System.Threading.Tasks;

namespace edventura_desktop.Services.Interfaces
{
    public interface IAuthService
    {
        Task<LoginResponse> LoginAsync(LoginRequest request);
        Task<LoginResponse> LoginAsync(string email, string password);
        Task<TokenRefreshResponse> RefreshTokenAsync(string refreshToken);
        Task<UserProfile> GetUserProfileAsync();
        Task<MfaSetupResponse> SetupMfaAsync();
        Task<bool> VerifyMfaAsync(string code);
        Task LogoutAsync(string? refreshToken = null);
    }
}