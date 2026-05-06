using System;
using System.Collections.Generic;
using System.Text;

namespace edventura_desktop.Models
{
    public class TokenRefreshResponse
    {
        public string access_token { get; set; } = "";
        public string refresh_token { get; set; } = "";
    }
}