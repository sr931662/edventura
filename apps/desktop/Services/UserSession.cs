using System;
using System.Collections.Generic;
using edventura_desktop.Models;

namespace edventura_desktop.Services
{
    public class UserSession
    {
        private static readonly Lazy<UserSession> _instance = new(() => new UserSession());
        public static UserSession Instance => _instance.Value;

        public string? AccessToken { get; private set; }
        public string? RefreshToken { get; private set; }
        public UserProfile? CurrentUser { get; private set; }

        public List<string> Permissions => CurrentUser?.permissions ?? new();
        public bool IsLoggedIn => CurrentUser != null;

        public event EventHandler? OnLoginSuccess;
        public event EventHandler? OnLogout;

        private UserSession() { }

        public void Login(string accessToken, string refreshToken, UserProfile user)
        {
            AccessToken = accessToken;
            RefreshToken = refreshToken;
            CurrentUser = user;
            OnLoginSuccess?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// Convenience overload: stores the profile without touching tokens
        /// (tokens live in TokenStorage / UserContext — this just makes the profile
        /// available to the UI layer such as ShellViewModel and DashboardViewModel).
        /// </summary>
        public void SetUserProfile(UserProfile profile)
        {
            CurrentUser = profile;
            OnLoginSuccess?.Invoke(this, EventArgs.Empty);
        }

        public void Logout()
        {
            AccessToken = null;
            RefreshToken = null;
            CurrentUser = null;
            OnLogout?.Invoke(this, EventArgs.Empty);
        }

        public bool HasPermission(string permission) =>
            Permissions.Contains(permission) || (CurrentUser?.is_super_admin ?? false);
    }
}