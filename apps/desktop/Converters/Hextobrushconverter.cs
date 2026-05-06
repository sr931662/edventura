using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace edventura_desktop.Converters
{
    /// <summary>
    /// Converts a "#RRGGBB" hex string to a SolidColorBrush.
    /// Use parameter "Transparent" to return Transparent on null/empty input.
    /// </summary>
    public class HexToBrushConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string hex && !string.IsNullOrWhiteSpace(hex))
            {
                try
                {
                    var color = (Color)ColorConverter.ConvertFromString(hex);
                    return new SolidColorBrush(color);
                }
                catch { /* fall through */ }
            }
            return Brushes.Transparent;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }

    /// <summary>
    /// Converts a "#RRGGBB" hex string to a Color struct.
    /// </summary>
    public class HexToColorConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string hex && !string.IsNullOrWhiteSpace(hex))
            {
                try { return (Color)ColorConverter.ConvertFromString(hex); }
                catch { }
            }
            return Colors.Transparent;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }

    /// <summary>
    /// Converts bool IsUp to a trend color brush (green = up, red = down).
    /// </summary>
    public class TrendColorConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
            => value is true
                ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#059669"))
                : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }
}