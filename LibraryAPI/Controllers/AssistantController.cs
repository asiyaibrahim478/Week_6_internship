using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using LibraryAPI.Services;

namespace LibraryAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class AssistantController : ControllerBase
    {
        private readonly IAiServiceClient _aiServiceClient;

        public AssistantController(IAiServiceClient aiServiceClient)
        {
            _aiServiceClient = aiServiceClient;
        }

        /// <summary>
        /// Resilient non-streaming assistant query with Polly retry and circuit breaker
        /// </summary>
        [HttpPost("ask")]
        [AllowAnonymous]
        public async Task<IActionResult> Ask([FromBody] AskRequestDto dto)
        {
            if (string.IsNullOrWhiteSpace(dto.Question) || dto.Question.Trim().Length < 3)
            {
                return BadRequest(new { message = "Question must be at least 3 characters long." });
            }

            try
            {
                var result = await _aiServiceClient.AskAsync(dto.Question, dto.SessionId);
                return Ok(result);
            }
            catch (BrokenCircuitException)
            {
                return StatusCode(StatusCodes.Status503ServiceUnavailable, new
                {
                    message = "The AI assistant is temporarily unavailable. Please try again shortly.",
                    status = "circuit_breaker_open",
                    retryAfterSeconds = 30
                });
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status503ServiceUnavailable, new
                {
                    message = "The AI assistant is temporarily unavailable.",
                    error = ex.Message
                });
            }
        }

        /// <summary>
        /// End-to-end SSE Streaming Proxy (FastAPI -> .NET -> Angular)
        /// </summary>
        [HttpPost("ask/stream")]
        [AllowAnonymous]
        public async Task AskStream([FromBody] AskRequestDto dto)
        {
            Response.ContentType = "text/event-stream";
            Response.Headers.Append("Cache-Control", "no-cache");
            Response.Headers.Append("Connection", "keep-alive");

            if (string.IsNullOrWhiteSpace(dto.Question) || dto.Question.Trim().Length < 3)
            {
                await Response.WriteAsync("data: Question must be at least 3 characters long.\n\n");
                await Response.WriteAsync("data: [DONE]\n\n");
                await Response.Body.FlushAsync();
                return;
            }

            try
            {
                var httpClient = _aiServiceClient.GetHttpClient();
                var upstreamRequest = new HttpRequestMessage(HttpMethod.Post, "/ask/stream")
                {
                    Content = JsonContent.Create(new { question = dto.Question, session_id = dto.SessionId ?? "stream-session" })
                };

                using var upstreamResponse = await httpClient.SendAsync(upstreamRequest, HttpCompletionOption.ResponseHeadersRead);
                
                if (!upstreamResponse.IsSuccessStatusCode)
                {
                    await Response.WriteAsync($"data: [Error: Downstream AI Service returned status {upstreamResponse.StatusCode}]\n\n");
                    await Response.WriteAsync("data: [DONE]\n\n");
                    await Response.Body.FlushAsync();
                    return;
                }

                await using var stream = await upstreamResponse.Content.ReadAsStreamAsync();
                using var reader = new StreamReader(stream);

                while (!reader.EndOfStream)
                {
                    var line = await reader.ReadLineAsync();
                    if (string.IsNullOrEmpty(line)) continue;

                    await Response.WriteAsync(line + "\n\n");
                    // Critical: Flush immediately to deliver tokens live to the frontend!
                    await Response.Body.FlushAsync();
                }
            }
            catch (BrokenCircuitException)
            {
                await Response.WriteAsync("data: The AI assistant is temporarily unavailable (circuit breaker open). Please try again shortly.\n\n");
                await Response.WriteAsync("data: [DONE]\n\n");
                await Response.Body.FlushAsync();
            }
            catch (Exception ex)
            {
                await Response.WriteAsync($"data: The AI service is currently unavailable ({ex.Message}).\n\n");
                await Response.WriteAsync("data: [DONE]\n\n");
                await Response.Body.FlushAsync();
            }
        }
    }
}
