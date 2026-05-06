using System;
using System.Windows;
using edventura_desktop.ViewModels.Dialogs;

namespace edventura_desktop.Views.Dialogs
{
    public partial class StudentDialog : Window
    {
        public StudentDialog(StudentDialogViewModel viewModel)
        {
            InitializeComponent();
            DataContext = viewModel;
            viewModel.RequestClose += (result) =>
            {
                DialogResult = result;
                Close();
            };
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            (DataContext as StudentDialogViewModel)?.CancelCommand.Execute(null);
        }

        private void Save_Click(object sender, RoutedEventArgs e)
        {
            (DataContext as StudentDialogViewModel)?.SaveCommand.Execute(null);
        }
    }
}