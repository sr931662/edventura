using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace edventura_desktop.Services
{
    public class ProtectionService
    {
        public void Save(string key, string value)
        {
            var bytes = Encoding.UTF8.GetBytes(value);
            var protectedBytes = ProtectedData.Protect(bytes, null, DataProtectionScope.CurrentUser);
            File.WriteAllBytes(GetFilePath(key), protectedBytes);
        }

        public string? Load(string key)
        {
            var path = GetFilePath(key);
            if (!File.Exists(path)) return null;
            var protectedBytes = File.ReadAllBytes(path);
            var bytes = ProtectedData.Unprotect(protectedBytes, null, DataProtectionScope.CurrentUser);
            return Encoding.UTF8.GetString(bytes);
        }

        public void Delete(string key) => File.Delete(GetFilePath(key));

        private string GetFilePath(string key) => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "EdVentura", key);
    }
}