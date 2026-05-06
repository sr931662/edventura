using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Models;
using edventura_desktop.Services;
using edventura_desktop.Services.Interfaces;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;

namespace edventura_desktop.ViewModels
{
    public partial class DaisyViewModel : ObservableObject
    {
        private readonly IDaisyService _daisyService;

        // ── State ──────────────────────────────────────────────────────────
        [ObservableProperty] private ObservableCollection<ChatMessage> _messages = new();
        [ObservableProperty] private string _inputText = "";
        [ObservableProperty] private bool _isOpen = false;
        [ObservableProperty] private bool _isThinking = false;
        [ObservableProperty] private bool _hasMessages = false;

        /// <summary>Raised when a new message is added — code-behind scrolls to bottom.</summary>
        public event Action? ScrollToBottomRequested;

        private ThemeService? Theme =>
            App.ServiceProvider.GetService<ThemeService>();

        public DaisyViewModel(IDaisyService daisyService)
        {
            _daisyService = daisyService;
        }

        // ── Commands ───────────────────────────────────────────────────────

        [RelayCommand]
        public void Toggle()
        {
            IsOpen = !IsOpen;
            if (IsOpen && Messages.Count == 0)
                ShowWelcome();
        }

        [RelayCommand]
        public void Close()
        {
            IsOpen = false;
        }

        [RelayCommand]
        private async Task SendAsync()
        {
            var text = InputText?.Trim();
            if (string.IsNullOrEmpty(text) || IsThinking) return;

            InputText = "";

            // Add user bubble
            AddMessage("user", text);

            IsThinking = true;
            try
            {
                // Pass all messages EXCEPT the one just added as history
                var history = Messages.SkipLast(1).ToList();
                var (reply, _) = await _daisyService.SendMessageAsync(text, history);
                AddMessage("assistant", reply);
            }
            catch
            {
                AddMessage("assistant",
                    "Oops, kuch toh problem hai 😅 Server se connect nahi ho pa raha. " +
                    "Please try again in a moment.");
            }
            finally
            {
                IsThinking = false;
            }
        }

        // ── Helpers ────────────────────────────────────────────────────────

        private void AddMessage(string role, string content)
        {
            Messages.Add(new ChatMessage
            {
                Role = role,
                Content = content,
                Timestamp = DateTime.Now
            });
            HasMessages = true;
            ScrollToBottomRequested?.Invoke();
        }

        private void ShowWelcome()
        {
            var name = UserSession.Instance.CurrentUser?.full_name?.Split(' ')[0] ?? "there";
            var role = Theme?.CurrentRole ?? AppRole.Default;

            string welcome = role switch
            {
                AppRole.SuperAdmin =>
                    $"Hi {name}! 🌼 I'm Daisy, your platform-wide guide.\n\n" +
                    "With full Super Admin access you can manage tenants, users, " +
                    "audit logs, and system health. What would you like to know?",

                AppRole.InstitutionOwner =>
                    $"Hi {name}! 🌼 Main Daisy hoon — aapka EdVentura guide.\n\n" +
                    "As an Institution Owner I can help you track revenue, compare " +
                    "campus performance, and navigate strategic reports. Kya chahiye?",

                AppRole.InstitutionAdmin =>
                    $"Hi {name}! 🌼 I'm Daisy — aapki campus operations guide.\n\n" +
                    "Main aapki help kar sakti hoon — students, staff, fees, notices, " +
                    "aur admissions mein. Kya problem hai aaj?",

                AppRole.InstitutionLeader =>
                    $"Hi {name}! 🌼 I'm Daisy, your academic assistant.\n\n" +
                    "I can guide you through exam scheduling, faculty management, " +
                    "syllabus tracking, and performance reports. How can I help?",

                AppRole.Student =>
                    $"Hi {name}! 🌼 Main Daisy hoon — tumhari EdVentura dost!\n\n" +
                    "Timetable, assignments, results, library — kuch bhi pucho. " +
                    "Main yahan hoon! 😊",

                _ =>
                    $"Hi {name}! 🌼 I'm Daisy, your EdVentura virtual assistant.\n\n" +
                    "Ask me anything about the platform — features, permissions, " +
                    "or where to find something!"
            };

            AddMessage("assistant", welcome);
        }
    }
}