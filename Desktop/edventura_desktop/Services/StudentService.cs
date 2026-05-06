using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using edventura_desktop.Models;

namespace edventura_desktop.Services
{
    public class StudentService
    {
        private readonly ApiClient _api;

        public StudentService(ApiClient api) => _api = api;

        public async Task<List<StudentDto>> GetStudentsAsync(bool isActive = true, int skip = 0, int limit = 100) =>
            await _api.GetAsync<List<StudentDto>>($"/api/v1/students/?is_active={isActive}&skip={skip}&limit={limit}") ?? new();

        public async Task<ImportResult> BulkImportStudentsAsync(byte[] csvContent)
        {
            var content = new MultipartFormDataContent();
            content.Add(new ByteArrayContent(csvContent), "file", "students.csv");
            var response = await _api.PostMultipartAsync("/api/v1/students/bulk-import", content);
            return await response.Content.ReadFromJsonAsync<ImportResult>();
        }
    }

    public class StudentDto
    {
        public string id { get; set; } = "";
        public string full_name { get; set; } = "";
        public string email { get; set; } = "";
        public string roll_number { get; set; } = "";
        public bool is_active { get; set; }
    }

    public class ImportResult
    {
        public int imported { get; set; }
        public List<string> errors { get; set; } = new();
    }
}