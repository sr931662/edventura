using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

namespace edventura_desktop.Services
{
    public class ApiClient
    {
        private readonly IHttpClientFactory _factory;

        public ApiClient(IHttpClientFactory factory) => _factory = factory;

        private HttpClient Create() => _factory.CreateClient("Backend");

        public async Task<T?> GetAsync<T>(string url)
        {
            var client = Create();
            return await client.GetFromJsonAsync<T>(url);
        }

        public async Task<TResponse?> PostAsJsonAsync<TRequest, TResponse>(string url, TRequest data)
        {
            var client = Create();
            var response = await client.PostAsJsonAsync(url, data);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<TResponse>();
        }

        public async Task<HttpResponseMessage> PatchAsJsonAsync<T>(string url, T data)
        {
            var client = Create();
            var request = new HttpRequestMessage(new HttpMethod("PATCH"), url)
            {
                Content = JsonContent.Create(data)
            };
            return await client.SendAsync(request);
        }

        public async Task DeleteAsync(string url)
        {
            var client = Create();
            var response = await client.DeleteAsync(url);
            response.EnsureSuccessStatusCode();
        }
    }
}