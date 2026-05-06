using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using edventura_desktop.Models;
using edventura_desktop.Services.Interfaces;

namespace edventura_desktop.Services
{
    public class DaisyService : IDaisyService
    {
        private readonly ApiClient _api;

        public DaisyService(ApiClient api) => _api = api;

        public async Task<(string Reply, string? Intent)> SendMessageAsync(
            string message,
            IEnumerable<ChatMessage> history)
        {
            var payload = new DaisyChatRequest
            {
                message = message,
                history = history
                    .TakeLast(20)   // stay within the 20-turn server limit
                    .Select(m => new DaisyChatHistoryItem
                    {
                        role = m.Role,
                        content = m.Content
                    })
                    .ToList()
            };

            try
            {
                var response = await _api.PostAsJsonAsync<DaisyChatRequest, DaisyChatResponse>(
                    "assistant/chat", payload);

                return (
                    response?.reply ?? FallbackReply(),
                    response?.intent
                );
            }
            catch (Exception ex) when (ex.Message.Contains("401") || ex.Message.Contains("Unauthorized"))
            {
                return ("Session expired. Please log out and log back in. 🔒", "general");
            }
            catch
            {
                return (FallbackReply(), "general");
            }
        }

        private static string FallbackReply() =>
            "I'm having trouble reaching the server right now 🔌 " +
            "Please make sure EdVentura backend is running and try again.";
    }
}