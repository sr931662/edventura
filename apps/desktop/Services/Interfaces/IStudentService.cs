using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using edventura_desktop.Models;
using edventura_desktop.Models.Requests;

namespace edventura_desktop.Services.Interfaces
{
    public interface IStudentService
    {
        Task<List<Student>> GetStudentsAsync(bool isActive = true, int skip = 0, int limit = 100);
        Task<Student?> GetStudentByIdAsync(Guid id);
        Task<Student> CreateStudentAsync(StudentCreateRequest request);
        Task<Student> UpdateStudentAsync(Guid id, StudentUpdateRequest request);
        Task DeleteStudentAsync(Guid id);
    }
}