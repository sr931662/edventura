using System;
using System.Net.NetworkInformation;

namespace edventura_desktop.Services
{
    public class ConnectivityService
    {
        public bool IsOnline => NetworkInterface.GetIsNetworkAvailable();
        public event Action<bool>? ConnectivityChanged;

        public ConnectivityService()
        {
            NetworkChange.NetworkAvailabilityChanged += (_, e) =>
                ConnectivityChanged?.Invoke(e.IsAvailable);
        }
    }
}