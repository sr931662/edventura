using System.Threading.Tasks;

namespace edventura_desktop.Services.Interfaces
{
    public class DashboardData
    {
        public int TotalStudents { get; set; }
        public int TotalTeachers { get; set; }
        public int TodayPresent { get; set; }
        public int TodayAbsent { get; set; }
    }

    public interface IDashboardService
    {
        Task<DashboardData> GetSummaryAsync();
    }
}