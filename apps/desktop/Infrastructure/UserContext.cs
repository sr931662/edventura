using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;

namespace EdVentura.Desktop.Infrastructure
{
    public class UserContext
    {
        public string? UserId { get; private set; }
        public string? TenantId { get; private set; }
        public List<string> Roles { get; private set; } = new();
        public List<string> Permissions { get; private set; } = new();

        public void SetFromAccessToken(string accessToken)
        {
            var parts = accessToken.Split('.');
            if (parts.Length != 3) return;

            var payload = parts[1];
            var padded = payload.PadRight(payload.Length + (4 - payload.Length % 4) % 4, '=');
            var json = Encoding.UTF8.GetString(Convert.FromBase64String(padded));

            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;

            UserId = root.TryGetProperty("sub", out var sub) ? sub.GetString() : null;
            TenantId = root.TryGetProperty("tenant_id", out var tid) ? tid.GetString() : null;
            Roles = root.TryGetProperty("roles", out var roles) && roles.ValueKind == JsonValueKind.Array
                ? roles.EnumerateArray().Select(r => r.GetString() ?? "").ToList()
                : new List<string>();
            Permissions = root.TryGetProperty("permissions", out var perms) && perms.ValueKind == JsonValueKind.Array
                ? perms.EnumerateArray().Select(p => p.GetString() ?? "").ToList()
                : new List<string>();
        }

        public void Clear()
        {
            UserId = null;
            TenantId = null;
            Roles.Clear();
            Permissions.Clear();
        }

        public bool HasPermission(string permission) => Permissions.Contains(permission);
    }
}
