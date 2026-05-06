using System;
using System.Collections.Generic;

namespace edventura_desktop.Services.Interfaces
{
    public class MenuItem
    {
        public string Title { get; set; } = "";
        public string Icon { get; set; } = "";
        public string? PermissionRequired { get; set; }
        public Type PageType { get; set; } = null!;
    }

    public interface IMenuService
    {
        IEnumerable<MenuItem> GetMenuItems();
    }
}