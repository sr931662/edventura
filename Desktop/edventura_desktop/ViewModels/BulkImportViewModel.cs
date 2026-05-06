using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using edventura_desktop.Services;

namespace edventura_desktop.ViewModels
{
    public partial class BulkImportViewModel : ObservableObject
    {
        private readonly StudentService _studentService;

        [ObservableProperty]
        private int progressValue;

        [ObservableProperty]
        private string statusText = "Ready to import.";

        [ObservableProperty]
        private string errorsText = "";

        public BulkImportViewModel(StudentService studentService) => _studentService = studentService;

        [RelayCommand]
        private async Task ImportAsync()
        {
            var dlg = new OpenFileDialog { Filter = "CSV files (*.csv)|*.csv" };
            if (dlg.ShowDialog() != true) return;
            StatusText = "Importing...";
            ErrorsText = "";
            ProgressValue = 0;
            var bytes = File.ReadAllBytes(dlg.FileName);
            var result = await _studentService.BulkImportStudentsAsync(bytes);
            StatusText = $"Imported {result.imported} students.";
            if (result.errors.Any())
                ErrorsText = string.Join("\n", result.errors);
        }
    }
}