using System.Windows.Controls;
using edventura_desktop.ViewModels;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.Views.Shell
{
    public partial class StudentListPage : Page
    {
        public StudentListPage()
        {
            InitializeComponent();
            var vm = App.ServiceProvider.GetRequiredService<StudentListViewModel>();
            DataContext = vm;
            Loaded += async (s, e) => await vm.LoadStudentsCommand.ExecuteAsync(null);
        }
    }
}