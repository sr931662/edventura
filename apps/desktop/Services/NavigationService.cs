using System;
using System.Windows.Controls;
using Microsoft.Extensions.DependencyInjection;
using edventura_desktop.Services.Interfaces;

namespace edventura_desktop.Services
{
    public class NavigationService : INavigationService
    {
        private readonly IServiceProvider _serviceProvider;
        private Frame? _mainFrame;

        public NavigationService(IServiceProvider serviceProvider)
        {
            _serviceProvider = serviceProvider;
        }

        public void SetMainFrame(Frame frame) => _mainFrame = frame;

        public void NavigateTo<T>() where T : Page
        {
            if (_mainFrame == null)
                throw new InvalidOperationException("MainFrame not set");
            var page = _serviceProvider.GetRequiredService<T>();
            _mainFrame.Navigate(page);
        }
    }
}