using System.Collections.Generic;
using System.Threading.Tasks;
using edventura_desktop.Models;

namespace edventura_desktop.Services.Interfaces
{
    public interface IDaisyService
    {
        Task<(string Reply, string? Intent)> SendMessageAsync(
            string message,
            IEnumerable<ChatMessage> history);
    }
}