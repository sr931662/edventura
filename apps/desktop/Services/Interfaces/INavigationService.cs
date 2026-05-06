using System.Windows.Controls;

namespace edventura_desktop.Services.Interfaces
{
    public interface INavigationService
    {
        void NavigateTo<T>() where T : Page;
    }
}