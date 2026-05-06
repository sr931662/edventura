using System;
using System.Collections.Generic;

namespace edventura_desktop.Models
{
    // ── Chat message (UI model) ───────────────────────────────────────────────
    public class ChatMessage
    {
        public string Role { get; set; } = "user";   // "user" | "assistant"
        public string Content { get; set; } = "";
        public DateTime Timestamp { get; set; } = DateTime.Now;

        // Computed helpers for XAML DataTrigger bindings
        public bool IsUser => Role == "user";
        public string TimeDisplay => Timestamp.ToString("HH:mm");
    }

    // ── API request / response DTOs ───────────────────────────────────────────
    public class DaisyChatHistoryItem
    {
        public string role { get; set; } = "";
        public string content { get; set; } = "";
    }

    public class DaisyChatRequest
    {
        public string message { get; set; } = "";
        public List<DaisyChatHistoryItem> history { get; set; } = new();
    }

    public class DaisyChatResponse
    {
        public string reply { get; set; } = "";
        public string? intent { get; set; }
        public string? timestamp { get; set; }
    }
}