using System;
using System.Collections.Generic;

namespace edventura_desktop.Models
{
    public class Student
    {
        public Guid id { get; set; }
        public string first_name { get; set; } = "";
        public string last_name { get; set; } = "";
        public string? middle_name { get; set; }
        public string full_name => $"{first_name} {last_name}".Trim();
        public string? class_name { get; set; }
        public string? section { get; set; }
        public string? roll_number { get; set; }
        public string? email { get; set; }
        public string? phone { get; set; }
        public bool is_active { get; set; }
    }
}