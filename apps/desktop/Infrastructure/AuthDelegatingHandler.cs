using System;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;

namespace EdVentura.Desktop.Infrastructure
{
    public class AuthDelegatingHandler : DelegatingHandler
    {
        private readonly TokenStorage _tokenStorage;
        private readonly IServiceProvider _serviceProvider;
        private static readonly SemaphoreSlim _refreshLock = new(1, 1);

        public AuthDelegatingHandler(TokenStorage tokenStorage, IServiceProvider serviceProvider)
        {
            _tokenStorage = tokenStorage;
            _serviceProvider = serviceProvider;
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var token = await _tokenStorage.GetAccessTokenAsync();
            if (!string.IsNullOrEmpty(token))
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

            var response = await base.SendAsync(request, cancellationToken);

            if (response.StatusCode == HttpStatusCode.Unauthorized && !request.RequestUri!.AbsolutePath.Contains("auth/refresh"))
            {
                await _refreshLock.WaitAsync(cancellationToken);
                try
                {
                    var refreshToken = await _tokenStorage.GetRefreshTokenAsync();
                    if (!string.IsNullOrEmpty(refreshToken))
                    {
                        var authService = _serviceProvider.GetRequiredService<edventura_desktop.Services.Interfaces.IAuthService>();
                        var newTokens = await authService.RefreshTokenAsync(refreshToken);
                        // Retry original request with new token
                        var clone = await CloneRequestAsync(request);
                        clone.Headers.Authorization = new AuthenticationHeaderValue("Bearer", newTokens.access_token);
                        response = await base.SendAsync(clone, cancellationToken);
                    }
                }
                catch
                {
                    // refresh failed; propagate 401 to caller
                }
                finally
                {
                    _refreshLock.Release();
                }
            }
            return response;
        }

        private static async Task<HttpRequestMessage> CloneRequestAsync(HttpRequestMessage request)
        {
            var clone = new HttpRequestMessage(request.Method, request.RequestUri);
            if (request.Content != null)
                clone.Content = await request.Content.ReadAsByteArrayAsync().ContinueWith(t => new ByteArrayContent(t.Result));
            foreach (var header in request.Headers)
                clone.Headers.TryAddWithoutValidation(header.Key, header.Value);
            return clone;
        }
    }
}