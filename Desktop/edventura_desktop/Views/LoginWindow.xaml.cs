using System.Windows;
using System.Windows.Controls;
using edventura_desktop.ViewModels;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.Views
{
    public partial class LoginWindow : Window
    {
        public LoginWindow()
        {
            InitializeComponent();
            var vm = App.ServiceProvider.GetRequiredService<LoginViewModel>();
            DataContext = vm;
            PasswordBox.PasswordChanged += (s, e) => vm.Password = PasswordBox.Password;
        }

        private void TogglePasswordVisibility(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Password visibility toggle not yet implemented.");
        }
    }
}
