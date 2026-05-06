using System.Collections.Generic;

namespace edventura_desktop.Models
{
    public class UserProfile
    {
        public string id { get; set; } = string.Empty;
        public string email { get; set; } = string.Empty;
        public string full_name { get; set; } = string.Empty;
        public string? phone { get; set; }
        public string? tenant_id { get; set; }
        public bool is_active { get; set; }
        public bool is_super_admin { get; set; }
        public List<string>? roles { get; set; }
    }
}