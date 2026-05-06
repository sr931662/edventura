namespace edventura_desktop.Models
{
    public class LoginRequest
    {
        public string email { get; set; } = string.Empty;
        public string password { get; set; } = string.Empty;
        public string? tenant_domain { get; set; }
        public string? mfa_code { get; set; }
    }
}
