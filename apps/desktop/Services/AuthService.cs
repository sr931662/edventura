using EdVentura.Desktop.Infrastructure;
using edventura_desktop.Models;
using edventura_desktop.Services.Interfaces;
using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

namespace edventura_desktop.Services
{
    public class AuthService : IAuthService
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly TokenStorage _tokenStorage;
        private readonly UserContext _userContext;

        public AuthService(IHttpClientFactory httpClientFactory, TokenStorage tokenStorage, UserContext userContext)
        {
            _httpClientFactory = httpClientFactory;
            _tokenStorage = tokenStorage;
            _userContext = userContext;
        }

        public Task<LoginResponse> LoginAsync(string email, string password)
            => LoginAsync(new LoginRequest { email = email, password = password });

        public async Task<LoginResponse> LoginAsync(LoginRequest request)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            var response = await client.PostAsJsonAsync("auth/login", request);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<LoginResponse>();
            if (result == null)
                throw new Exception("Invalid server response");

            if (!string.IsNullOrEmpty(result.access_token))
            {
                await _tokenStorage.SaveTokensAsync(result.access_token, result.refresh_token);
                _userContext.SetFromAccessToken(result.access_token);
            }
            return result;
        }

        public async Task<TokenRefreshResponse> RefreshTokenAsync(string refreshToken)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            var request = new { refresh_token = refreshToken };
            var response = await client.PostAsJsonAsync("auth/refresh", request);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<TokenRefreshResponse>();
            if (result == null)
                throw new Exception("Invalid refresh response");

            await _tokenStorage.SaveTokensAsync(result.access_token, result.refresh_token);
            _userContext.SetFromAccessToken(result.access_token);
            return result;
        }

        public async Task<UserProfile> GetUserProfileAsync()
        {
            var client = _httpClientFactory.CreateClient("Backend");
            var response = await client.GetAsync("auth/me");
            response.EnsureSuccessStatusCode();
            var profile = await response.Content.ReadFromJsonAsync<UserProfile>();
            return profile ?? throw new Exception("Invalid profile response");
        }

        public async Task<MfaSetupResponse> SetupMfaAsync()
        {
            var client = _httpClientFactory.CreateClient("Backend");
            var response = await client.PostAsync("auth/mfa/setup", null);
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<MfaSetupResponse>();
            return result ?? throw new Exception("Invalid MFA setup response");
        }

        public async Task<bool> VerifyMfaAsync(string code)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            var response = await client.PostAsJsonAsync("auth/mfa/verify", new { code });
            return response.IsSuccessStatusCode;
        }

        public async Task LogoutAsync(string? refreshToken = null)
        {
            try
            {
                var client = _httpClientFactory.CreateClient("Backend");
                if (!string.IsNullOrEmpty(refreshToken))
                {
                    await client.PostAsJsonAsync("auth/logout", new { refresh_token = refreshToken });
                }
            }
            catch { /* ignore network errors during logout */ }
            finally
            {
                await _tokenStorage.ClearAsync();
                _userContext.Clear();
            }
        }
    }
}