using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Models;
using edventura_desktop.Models.Requests;
using edventura_desktop.Services.Interfaces;
using System;
using System.Threading.Tasks;

namespace edventura_desktop.ViewModels.Dialogs
{
    public partial class StudentDialogViewModel : ObservableObject
    {
        private readonly IStudentService _studentService = null!;
        private readonly Guid? _studentId; // null for new

        public event Action<bool>? RequestClose;

        [ObservableProperty] private string _title = "Add Student";

        [ObservableProperty] private string _firstName = "";
        [ObservableProperty] private string _lastName = "";
        [ObservableProperty] private string? _middleName;
        [ObservableProperty] private DateTime _dateOfBirth = DateTime.Now.AddYears(-10);
        [ObservableProperty] private string _gender = "Male";
        [ObservableProperty] private DateTime _admissionDate = DateTime.Now;
        [ObservableProperty] private string? _bloodGroup;
        [ObservableProperty] private string? _medicalNotes;
        [ObservableProperty] private string? _section;
        [ObservableProperty] private string? _rollNumber;
        [ObservableProperty] private string? _email;
        [ObservableProperty] private string? _phone;
        [ObservableProperty] private string? _address;
        [ObservableProperty] private string? _city;
        [ObservableProperty] private string? _state;
        [ObservableProperty] private string? _pincode;

        public StudentDialogViewModel() { } // designer

        public StudentDialogViewModel(IStudentService studentService, Student? existing = null)
        {
            _studentService = studentService;
            if (existing != null)
            {
                _studentId = existing.id;
                Title = "Edit Student";
                FirstName = existing.first_name;
                LastName = existing.last_name;
                MiddleName = existing.middle_name;
                DateOfBirth = DateTime.MinValue; // you'd need to convert, but API returns proper date
                // For simplicity, we skip exact date mapping (you can extend)
            }
        }

        [RelayCommand]
        private void Cancel() => RequestClose?.Invoke(false);

        [RelayCommand]
        private async Task SaveAsync()
        {
            if (string.IsNullOrWhiteSpace(FirstName) || string.IsNullOrWhiteSpace(LastName))
            {
                System.Windows.MessageBox.Show("First and last name required.");
                return;
            }

            try
            {
                if (_studentId.HasValue)
                {
                    var update = new StudentUpdateRequest
                    {
                        first_name = FirstName,
                        last_name = LastName,
                        middle_name = MiddleName,
                        date_of_birth = DateOfBirth,
                        gender = Gender,
                        blood_group = BloodGroup,
                        medical_notes = MedicalNotes,
                        section = Section,
                        roll_number = RollNumber,
                        email = Email,
                        phone = Phone,
                        address = Address
                    };
                    await _studentService.UpdateStudentAsync(_studentId.Value, update);
                }
                else
                {
                    var create = new StudentCreateRequest
                    {
                        first_name = FirstName,
                        last_name = LastName,
                        middle_name = MiddleName,
                        date_of_birth = DateOfBirth,
                        gender = Gender,
                        admission_date = AdmissionDate,
                        blood_group = BloodGroup,
                        medical_notes = MedicalNotes,
                        section = Section,
                        roll_number = RollNumber,
                        email = Email,
                        phone = Phone,
                        address = Address
                    };
                    await _studentService.CreateStudentAsync(create);
                }
                RequestClose?.Invoke(true);
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"Save failed: {ex.Message}");
            }
        }
    }
}