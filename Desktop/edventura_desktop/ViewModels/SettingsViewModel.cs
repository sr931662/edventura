using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Services;

namespace edventura_desktop.ViewModels
{
    public partial class SettingsViewModel : ObservableObject
    {
        private readonly AttendanceService _attendanceService;

        [ObservableProperty]
        private int lateGraceMinutes = 15;

        [ObservableProperty]
        private double minAttendancePercent = 75;

        public SettingsViewModel(AttendanceService attendanceService)
        {
            _attendanceService = attendanceService;
            _ = LoadPolicy();
        }

        private async Task LoadPolicy()
        {
            var policy = await _attendanceService.GetPolicyAsync();
            if (policy != null)
            {
                LateGraceMinutes = policy.late_grace_minutes;
                MinAttendancePercent = policy.min_attendance_percent;
            }
        }

        [RelayCommand]
        private async Task SavePolicyAsync()
        {
            var policy = new AttendancePolicy
            {
                late_grace_minutes = LateGraceMinutes,
                min_attendance_percent = (int)MinAttendancePercent
            };
            await _attendanceService.UpdatePolicyAsync(policy);
        }
    }
}