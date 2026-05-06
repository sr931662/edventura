using System.Collections.Generic;

namespace edventura_desktop.Models
{
    public class UserProfile
    {
        public string id { get; set; } = "";
        public string email { get; set; } = "";
        public string full_name { get; set; } = "";
        public string? phone { get; set; }
        public string? tenant_id { get; set; }
        public bool is_active { get; set; }
        public bool is_super_admin { get; set; }
        public List<string>? roles { get; set; }
        public List<string>? permissions { get; set; }   // added
    }
}