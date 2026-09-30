using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace LibraryAPI.Services
{
    public class BrokenCircuitException : Exception
    {
        public BrokenCircuitException(string message) : base(message) { }
    }

    /// <summary>
    /// Implements Exponential Backoff Retry and Circuit Breaker DelegatingHandler
    /// Matching the Week 6 Polly pattern with zero external dependencies.
    /// </summary>
    public class ResilientPolicyDelegatingHandler : DelegatingHandler
    {
        private static int _consecutiveFailures = 0;
        private static DateTime _circuitOpenedAt = DateTime.MinValue;
        private static readonly TimeSpan BreakDuration = TimeSpan.FromSeconds(30);
        private const int AllowedFailures = 3;

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // 1. Circuit Breaker Check
            if (_consecutiveFailures >= AllowedFailures)
            {
                if (DateTime.UtcNow - _circuitOpenedAt < BreakDuration)
                {
                    throw new BrokenCircuitException("The circuit is broken. Downstream AI service is currently unavailable.");
                }
                else
                {
                    // Half-Open state: Allow probe request
                    _consecutiveFailures = AllowedFailures - 1;
                }
            }

            // 2. Exponential Backoff Retry Policy (3 attempts)
            HttpResponseMessage? response = null;
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                try
                {
                    response = await base.SendAsync(request, cancellationToken);
                    if (response.IsSuccessStatusCode)
                    {
                        // Reset failure counter on success
                        _consecutiveFailures = 0;
                        return response;
                    }
                }
                catch (Exception) when (attempt < 3)
                {
                    // Wait with exponential backoff: 2^attempt seconds (e.g. 2s, 4s)
                    await Task.Delay(TimeSpan.FromSeconds(Math.Pow(2, attempt)), cancellationToken);
                }
            }

            // Trip Circuit Breaker if failure threshold reached
            _consecutiveFailures++;
            if (_consecutiveFailures >= AllowedFailures)
            {
                _circuitOpenedAt = DateTime.UtcNow;
            }

            return response ?? throw new HttpRequestException("Failed to reach AI service after retries.");
        }
    }
}
