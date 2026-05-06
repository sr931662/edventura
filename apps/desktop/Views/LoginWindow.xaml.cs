using System.Windows;
using System.Windows.Input;
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
            vm.LoginSucceeded += () =>
            {
                var shell = App.ServiceProvider.GetRequiredService<ShellWindow>();
                shell.Show();
                this.Close(); // Use this.Close() to refer to the instance method
            };
        }

        // --- Custom Title Bar Window Control Methods ---

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            // Allows the user to drag the window by clicking and holding the custom title bar
            if (e.ChangedButton == MouseButton.Left)
            {
                this.DragMove();
            }
        }

        private void Minimize_Click(object sender, RoutedEventArgs e)
        {
            // Minimizes the window to the taskbar
            this.WindowState = WindowState.Minimized;
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            // Closes the application/window
            this.Close();
        }

        // --- Existing Event Handlers ---

        private void TogglePasswordVisibility(object sender, RoutedEventArgs e) { }
        private void ForgotPassword_Click(object sender, MouseButtonEventArgs e) { }
        private void FaceId_Click(object sender, MouseButtonEventArgs e) { }
        private void Biometric_Click(object sender, MouseButtonEventArgs e) { }
    }
}