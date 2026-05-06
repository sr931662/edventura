using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using edventura_desktop.Models;
using edventura_desktop.Services.Interfaces;
using edventura_desktop.Views.Dialogs;  // needed to open dialog
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.ViewModels
{
    public partial class StudentListViewModel : ObservableObject
    {
        private readonly IStudentService _studentService;

        [ObservableProperty]
        private ObservableCollection<Student> _students = new();

        [ObservableProperty]
        private Student? _selectedStudent;

        [ObservableProperty]
        private bool _isLoading;

        public StudentListViewModel(IStudentService studentService)
        {
            _studentService = studentService;
        }

        [RelayCommand]
        private async Task LoadStudentsAsync()
        {
            IsLoading = true;
            try
            {
                var list = await _studentService.GetStudentsAsync();
                Students.Clear();
                foreach (var s in list)
                    Students.Add(s);
            }
            finally
            {
                IsLoading = false;
            }
        }

        [RelayCommand]
        private async Task AddStudentAsync()
        {
            var dialogVm = new Dialogs.StudentDialogViewModel(_studentService);
            var dialog = new StudentDialog(dialogVm) { Owner = Application.Current.MainWindow };
            var result = dialog.ShowDialog();
            if (result == true)
                await LoadStudentsAsync();
        }

        [RelayCommand]
        private async Task EditStudentAsync()
        {
            if (SelectedStudent == null) return;
            var dialogVm = new Dialogs.StudentDialogViewModel(_studentService, SelectedStudent);
            var dialog = new StudentDialog(dialogVm) { Owner = Application.Current.MainWindow };
            var result = dialog.ShowDialog();
            if (result == true)
                await LoadStudentsAsync();
        }

        [RelayCommand]
        private async Task DeleteStudentAsync()
        {
            if (SelectedStudent == null) return;
            var confirm = MessageBox.Show(
                $"Delete {SelectedStudent.full_name}?",
                "Confirm Delete",
                MessageBoxButton.YesNo, MessageBoxImage.Warning);
            if (confirm != MessageBoxResult.Yes) return;

            try
            {
                await _studentService.DeleteStudentAsync(SelectedStudent.id);
                Students.Remove(SelectedStudent);
                SelectedStudent = null;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Delete failed: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}