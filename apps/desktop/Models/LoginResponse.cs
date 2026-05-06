namespace edventura_desktop.Models
{
    public class LoginResponse
    {
        public string access_token { get; set; } = "";
        public string refresh_token { get; set; } = "";
        public bool mfa_required { get; set; }
        public string? user_id { get; set; }
    }
}