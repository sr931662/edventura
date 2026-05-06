using System.Threading.Tasks;
using edventura_desktop.Services.Interfaces;

namespace edventura_desktop.Services
{
    public class DashboardService : IDashboardService
    {
        private readonly ApiClient _api;

        public DashboardService(ApiClient api) => _api = api;

        public async Task<DashboardData> GetSummaryAsync()
        {
            // This endpoint should exist on backend; for now we return mock data
            return await Task.FromResult(new DashboardData
            {
                TotalStudents = 12,
                TotalTeachers = 4,
                TodayPresent = 10,
                TodayAbsent = 2
            });
        }
    }
}