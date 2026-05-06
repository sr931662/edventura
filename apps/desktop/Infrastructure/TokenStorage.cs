using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace EdVentura.Desktop.Infrastructure
{
    public class TokenStorage
    {
        private static readonly string BasePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "EdVentura");

        private static readonly string TokensFile = Path.Combine(BasePath, "tokens.dat");
        private static readonly string EmailFile = Path.Combine(BasePath, "email.dat");

        private record TokenData(string? access_token, string? refresh_token);

        public async Task SaveTokensAsync(string accessToken, string refreshToken)
        {
            Directory.CreateDirectory(BasePath);
            var json = JsonSerializer.Serialize(new TokenData(accessToken, refreshToken));
            var encrypted = ProtectedData.Protect(Encoding.UTF8.GetBytes(json), null, DataProtectionScope.CurrentUser);
            await File.WriteAllBytesAsync(TokensFile, encrypted);
        }

        public async Task<(string? AccessToken, string? RefreshToken)> LoadTokensAsync()
        {
            if (!File.Exists(TokensFile)) return (null, null);
            var encrypted = await File.ReadAllBytesAsync(TokensFile);
            try
            {
                var json = Encoding.UTF8.GetString(ProtectedData.Unprotect(encrypted, null, DataProtectionScope.CurrentUser));
                var data = JsonSerializer.Deserialize<TokenData>(json);
                return (data?.access_token, data?.refresh_token);
            }
            catch
            {
                return (null, null);
            }
        }

        public async Task<string?> GetAccessTokenAsync()
        {
            var (access, _) = await LoadTokensAsync();
            return access;
        }

        public async Task<string?> GetRefreshTokenAsync()
        {
            var (_, refresh) = await LoadTokensAsync();
            return refresh;
        }

        public async Task SaveEmailAsync(string email)
        {
            Directory.CreateDirectory(BasePath);
            var encrypted = ProtectedData.Protect(Encoding.UTF8.GetBytes(email), null, DataProtectionScope.CurrentUser);
            await File.WriteAllBytesAsync(EmailFile, encrypted);
        }

        public async Task<string?> LoadEmailAsync()
        {
            if (!File.Exists(EmailFile)) return null;
            var encrypted = await File.ReadAllBytesAsync(EmailFile);
            try
            {
                return Encoding.UTF8.GetString(ProtectedData.Unprotect(encrypted, null, DataProtectionScope.CurrentUser));
            }
            catch
            {
                return null;
            }
        }

        public async Task ClearAsync()
        {
            if (File.Exists(TokensFile)) File.Delete(TokensFile);
        }

        public void ClearEmail()
        {
            if (File.Exists(EmailFile)) File.Delete(EmailFile);
        }
    }
}
