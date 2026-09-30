// Week 6 Part E: Typed HTTP Client Implementation Calling FastAPI AI Service
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

        public async Task<AskResponseDto> AskAsync(string question, string? sessionId = null)
        {
            var payload = new { question = question, session_id = sessionId ?? "default-user" };
            var response = await _httpClient.PostAsJsonAsync("/ask", payload);

            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<AskResponseDto>();
            return result ?? new AskResponseDto("No response received from AI service.", Array.Empty<string>(), "low");
        }
    }
}
