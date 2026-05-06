using System.Threading.Tasks;

namespace edventura_desktop.Services
{
    public class AttendanceService
    {
        private readonly ApiClient _api;

        public AttendanceService(ApiClient api) => _api = api;

        public async Task<AttendancePolicy> GetPolicyAsync() =>
            await _api.GetAsync<AttendancePolicy>("/api/v1/attendance/policy");

        public async Task UpdatePolicyAsync(AttendancePolicy policy) =>
            await _api.PutAsJsonAsync("/api/v1/attendance/policy", policy);
    }

    public class AttendancePolicy
    {
        public int late_grace_minutes { get; set; } = 15;
        public int half_day_threshold_hours { get; set; } = 3;
        public int min_attendance_percent { get; set; } = 75;
        public string[]? enabled_marking_methods { get; set; }
    }
}