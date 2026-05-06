namespace edventura_desktop.Models
{
    public class StatCard
    {
        public string Icon { get; set; } = "";
        public string Label { get; set; } = "";
        public string Value { get; set; } = "";
        public string Trend { get; set; } = "";
        public bool IsUp { get; set; } = true;
        public string IconBg { get; set; } = "#EFF6FF";
        public string IconColor { get; set; } = "#3B82F6";
    }

    public class ActivityItem
    {
        public string DotColor { get; set; } = "#3B82F6";
        public string Icon { get; set; } = "●";
        public string Title { get; set; } = "";
        public string Description { get; set; } = "";
        public string TimeAgo { get; set; } = "";
    }

    public class QuickAction
    {
        public string Icon { get; set; } = "";
        public string Label { get; set; } = "";
        public string Bg { get; set; } = "#EFF6FF";
        public string Fg { get; set; } = "#3B82F6";
    }

    public class ScheduleItem
    {
        public string Time { get; set; } = "";
        public string Subject { get; set; } = "";
        public string Room { get; set; } = "";
        public bool IsNow { get; set; } = false;
        public bool IsFree { get; set; } = false;
    }
}