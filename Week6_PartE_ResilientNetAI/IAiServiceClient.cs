// Week 6 Part E: Typed AI Service Client Interface
using System.Threading.Tasks;

namespace LibraryAPI.Services
{
    public record AskRequestDto(string Question, string? SessionId = null);
    
    public record AskResponseDto(string Answer, string[] Sources, string? Confidence = "high");

    public interface IAiServiceClient
    {
        Task<AskResponseDto> AskAsync(string question, string? sessionId = null);
    }
}
