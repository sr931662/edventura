using System.Windows.Controls;
using edventura_desktop.ViewModels;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.Views
{
    public partial class ProfilePage : UserControl
    {
        public ProfilePage()
        {
            InitializeComponent();
            var vm = App.ServiceProvider.GetRequiredService<ProfileViewModel>();
            DataContext = vm;
            Loaded += async (s, e) => await vm.LoadProfileCommand.ExecuteAsync(null);
        }
    }
}