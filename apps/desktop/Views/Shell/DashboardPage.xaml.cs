using System.Windows.Controls;
using edventura_desktop.ViewModels;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.Views.Shell
{
    public partial class DashboardPage : Page
    {
        public DashboardPage()
        {
            InitializeComponent();
            var vm = App.ServiceProvider.GetRequiredService<DashboardViewModel>();
            DataContext = vm;
            Loaded += async (s, e) => await vm.LoadDataCommand.ExecuteAsync(null);
        }
    }
}