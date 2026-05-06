using System.Windows.Controls;
using edventura_desktop.ViewModels;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.Views
{
    public partial class UsersPage : UserControl
    {
        public UsersPage()
        {
            InitializeComponent();
            DataContext = App.ServiceProvider.GetRequiredService<UsersViewModel>();
        }
    }
}