using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Threading;
using System.Threading.Tasks;
using edventura_desktop.Models;
using Microsoft.Extensions.DependencyInjection;

namespace edventura_desktop.Services
{
    public class ApiClient
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly ProtectionService _protection;  // not used directly, but available

        public ApiClient(IHttpClientFactory httpClientFactory, ProtectionService protection)
        {
            _httpClientFactory = httpClientFactory;
            _protection = protection;
        }

        public async Task<T?> GetAsync<T>(string uri)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            return await client.GetFromJsonAsync<T>(uri);
        }

        public async Task<HttpResponseMessage> PostAsJsonAsync<T>(string uri, T value)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            return await client.PostAsJsonAsync(uri, value);
        }

        public async Task<TResponse?> PostAsJsonAsync<TRequest, TResponse>(string uri, TRequest request)
        {
            var response = await PostAsJsonAsync(uri, request);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<TResponse>();
        }

        public async Task<HttpResponseMessage> PutAsJsonAsync<T>(string uri, T value)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            return await client.PutAsJsonAsync(uri, value);
        }

        public async Task<HttpResponseMessage> DeleteAsync(string uri)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            return await client.DeleteAsync(uri);
        }

        public async Task<HttpResponseMessage> PostMultipartAsync(string uri, MultipartContent content)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            return await client.PostAsync(uri, content);
        }

        public async Task<byte[]> GetByteArrayAsync(string uri)
        {
            var client = _httpClientFactory.CreateClient("Backend");
            return await client.GetByteArrayAsync(uri);
        }
    }

    public class AuthenticationDelegatingHandler : DelegatingHandler
    {
        private readonly ProtectionService _protection;
        private readonly AuthService _authService;
        private static readonly SemaphoreSlim _lock = new SemaphoreSlim(1, 1);

        public AuthenticationDelegatingHandler(ProtectionService protection, IServiceProvider sp)
            : this(protection, sp.GetRequiredService<AuthService>()) { }

        public AuthenticationDelegatingHandler(ProtectionService protection, AuthService authService)
        {
            _protection = protection;
            _authService = authService;
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var accessToken = _protection.Load("access_token");
            if (!string.IsNullOrEmpty(accessToken))
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

            var response = await base.SendAsync(request, cancellationToken);

            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            {
                await _lock.WaitAsync(cancellationToken);
                try
                {
                    var newToken = await _authService.RefreshTokenAsync();
                    if (!string.IsNullOrEmpty(newToken))
                    {
                        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", newToken);
                        response = await base.SendAsync(request, cancellationToken);
                    }
                }
                finally
                {
                    _lock.Release();
                }
            }
            return response;
        }
    }
}