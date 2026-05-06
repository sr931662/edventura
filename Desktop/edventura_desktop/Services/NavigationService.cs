using System;
using System.Collections.Generic;
using System.Windows.Controls;

namespace edventura_desktop.Services
{
    public class NavigationService
    {
        private ContentControl? _contentArea;
        private readonly Dictionary<string, UserControl> _pages = new();

        public void SetContentArea(ContentControl contentArea)
        {
            _contentArea = contentArea;
        }

        public void RegisterPage(string key, UserControl page)
        {
            _pages[key] = page;
        }

        public void NavigateTo(string key)
        {
            if (_contentArea != null && _pages.ContainsKey(key))
            {
                _contentArea.Content = _pages[key];
            }
        }
    }
}