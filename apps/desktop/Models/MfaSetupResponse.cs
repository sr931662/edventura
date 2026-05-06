namespace edventura_desktop.Models
{
    public class MfaSetupResponse
    {
        public string secret { get; set; } = "";
        public string qr_code_uri { get; set; } = "";
    }
}