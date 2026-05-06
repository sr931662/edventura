using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using edventura_desktop.Models;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.Services
{
    public class AuthService
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly ProtectionService _protection;
        private readonly IServiceProvider _serviceProvider;

        public UserProfile? CurrentUser { get; private set; }
        public event Action? UserLoggedIn;
        public event Action? UserLoggedOut;

        public AuthService(IHttpClientFactory httpClientFactory, ProtectionService protection, IServiceProvider serviceProvider)
        {
            _httpClientFactory = httpClientFactory;
            _protection = protection;
            _serviceProvider = serviceProvider;
        }

        public async Task LoginAsync(string email, string password)
        {
            // Use a short-lived client without the token handler
            var client = _httpClientFactory.CreateClient();
            var response = await client.PostAsJsonAsync("http://localhost:8000/api/v1/auth/login",
                new LoginRequest { email = email, password = password });
            response.EnsureSuccessStatusCode();
            var token = await response.Content.ReadFromJsonAsync<TokenResponse>();
            if (token == null) throw new Exception("Invalid response");

            _protection.Save("access_token", token.access_token);
            _protection.Save("refresh_token", token.refresh_token);

            // Fetch user profile using the normal client (which will now have the token)
            var apiClient = _serviceProvider.GetRequiredService<ApiClient>();
            CurrentUser = await apiClient.GetAsync<UserProfile>("/api/v1/auth/me");
            if (CurrentUser == null) throw new Exception("Failed to fetch user");

            UserLoggedIn?.Invoke();
        }

        public async Task<string?> RefreshTokenAsync()
        {
            var refreshToken = _protection.Load("refresh_token");
            if (string.IsNullOrEmpty(refreshToken)) return null;

            var client = _httpClientFactory.CreateClient();
            var response = await client.PostAsJsonAsync("http://localhost:8000/api/v1/auth/refresh",
                new { refresh_token = refreshToken });
            if (!response.IsSuccessStatusCode) return null;

            var token = await response.Content.ReadFromJsonAsync<TokenResponse>();
            if (token == null) return null;

            _protection.Save("access_token", token.access_token);
            if (token.refresh_token != null)
                _protection.Save("refresh_token", token.refresh_token);
            return token.access_token;
        }

        public void Logout()
        {
            _protection.Delete("access_token");
            _protection.Delete("refresh_token");
            CurrentUser = null;
            UserLoggedOut?.Invoke();
        }
    }
}