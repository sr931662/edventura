namespace edventura_desktop.Models
{
    public class TokenResponse
    {
        public string access_token { get; set; } = string.Empty;
        public string refresh_token { get; set; } = string.Empty;
        public string token_type { get; set; } = "bearer";
    }
}