// Week 6 Part E: AssistantController with Circuit Breaker Handling & Graceful Degradation
using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using LibraryAPI.Services;
using Polly.CircuitBreaker;

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

        [HttpPost("ask")]
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
                // Graceful degradation when circuit breaker is open (downstream AI service failing repeatedly)
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
                    message = "The AI service encountered a temporary error.",
                    error = ex.Message
                });
            }
        }
    }
}
