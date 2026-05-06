using System;
using System.Globalization;
using System.Windows.Data;

namespace edventura_desktop.Helpers
{
    public class StringToLoginTextConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool busy && busy)
                return "A U T H E N T I C A T I N G . . .";
            return "L O G I N";
        }
        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }
}