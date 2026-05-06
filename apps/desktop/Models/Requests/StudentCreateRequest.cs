using System;

namespace edventura_desktop.Models.Requests
{
    public class StudentCreateRequest
    {
        public string first_name { get; set; } = "";
        public string last_name { get; set; } = "";
        public string? middle_name { get; set; }
        public DateTime date_of_birth { get; set; }
        public string gender { get; set; } = "Male";
        public DateTime admission_date { get; set; }
        public string? blood_group { get; set; }
        public string? medical_notes { get; set; }
        public Guid? class_id { get; set; }
        public string? section { get; set; }
        public string? roll_number { get; set; }
        public string? email { get; set; }
        public string? phone { get; set; }
        public string? address { get; set; }
        public string? city { get; set; }
        public string? state { get; set; }
        public string? pincode { get; set; }
    }
}