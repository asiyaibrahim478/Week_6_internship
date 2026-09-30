using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

namespace LibraryAPI.Services
{
    public class AiServiceClient : IAiServiceClient
    {
        private readonly HttpClient _httpClient;

        public AiServiceClient(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        public HttpClient GetHttpClient() => _httpClient;

        public async Task<AskResponseDto> AskAsync(string question, string? sessionId = null)
        {
            var payload = new { question = question, session_id = sessionId ?? "default-session" };
            var response = await _httpClient.PostAsJsonAsync("/ask", payload);

            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<AskResponseDto>();
            return result ?? new AskResponseDto("No answer returned from AI service.", Array.Empty<string>(), "low");
        }
    }
}
