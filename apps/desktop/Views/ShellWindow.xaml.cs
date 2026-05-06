using Microsoft.Extensions.DependencyInjection;
using System.Windows;
using System.Windows.Input;
using edventura_desktop.Services;
using edventura_desktop.Services.Interfaces;
using edventura_desktop.ViewModels;
using edventura_desktop.Views.Shell;

namespace edventura_desktop.Views
{
    public partial class ShellWindow : System.Windows.Window
    {
        public ShellWindow(ShellViewModel viewModel, INavigationService navigationService)
        {
            InitializeComponent();
            DataContext = viewModel;

            if (navigationService is NavigationService nav)
                nav.SetMainFrame(MainFrame);

            navigationService.NavigateTo<DashboardPage>();
        }

        // --- Custom Title Bar Controls ---

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2)
            {
                Maximize_Click(sender, e);
            }
            else if (e.ChangedButton == MouseButton.Left)
            {
                this.DragMove();
            }
        }

        private void Minimize_Click(object sender, RoutedEventArgs e)
        {
            this.WindowState = System.Windows.WindowState.Minimized;
        }

        private void Maximize_Click(object sender, RoutedEventArgs e)
        {
            if (this.WindowState == System.Windows.WindowState.Normal)
                this.WindowState = System.Windows.WindowState.Maximized;
            else
                this.WindowState = System.Windows.WindowState.Normal;
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        // ── Daisy AI panel ────────────────────────────────────────────────────

        private DaisyViewModel? _daisyVm;

        private void EnsureDaisy()
        {
            if (_daisyVm != null) return;
            _daisyVm = App.ServiceProvider.GetRequiredService<DaisyViewModel>();
            DaisyPanelCtrl.DataContext = _daisyVm;
            _daisyVm.PropertyChanged += (_, e) =>
            {
                if (e.PropertyName == nameof(DaisyViewModel.IsOpen))
                    DaisyBackdrop.Visibility = _daisyVm.IsOpen
                        ? Visibility.Visible : Visibility.Collapsed;
            };
        }

        private void AskDaisy_Click(object sender, RoutedEventArgs e)
        {
            EnsureDaisy();
            _daisyVm!.ToggleCommand.Execute(null);
        }

        private void DaisyBackdrop_Click(object sender, MouseButtonEventArgs e)
        {
            _daisyVm?.CloseCommand.Execute(null);
        }
    }
}