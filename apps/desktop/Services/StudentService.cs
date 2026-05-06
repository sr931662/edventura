using edventura_desktop.Models;
using edventura_desktop.Models.Requests;
using edventura_desktop.Services.Interfaces;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

namespace edventura_desktop.Services
{
    public class StudentService : IStudentService
    {
        private readonly ApiClient _api;

        public StudentService(ApiClient api) => _api = api;

        public async Task<List<Student>> GetStudentsAsync(bool isActive = true, int skip = 0, int limit = 100)
        {
            var result = await _api.GetAsync<List<Student>>(
                $"students?is_active={isActive}&skip={skip}&limit={limit}");
            return result ?? new List<Student>();
        }

        public async Task<Student?> GetStudentByIdAsync(Guid id)
            => await _api.GetAsync<Student>($"students/{id}");

        public async Task<Student> CreateStudentAsync(StudentCreateRequest request)
            => await _api.PostAsJsonAsync<StudentCreateRequest, Student>("students", request)
               ?? throw new Exception("Failed to create student");

        public async Task<Student> UpdateStudentAsync(Guid id, StudentUpdateRequest request)
        {
            var response = await _api.PatchAsJsonAsync($"students/{id}", request);
            response.EnsureSuccessStatusCode();
            var student = await response.Content.ReadFromJsonAsync<Student>();
            return student ?? throw new Exception("Failed to update student");
        }

        public async Task DeleteStudentAsync(Guid id)
            => await _api.DeleteAsync($"students/{id}");
    }
}