# Week 6 — Part E: Resilient .NET $\rightarrow$ AI Service Integration

## Overview
Microservice communication between .NET Web API and Python FastAPI requires production-grade resilience to prevent network glitches or slow AI responses from cascading into system-wide outages.

---

## 🛡️ Polly Resilience Architecture

### 1. Exponential Backoff Retry Policy
- **Why not immediate retries?** If a downstream service is struggling under heavy CPU load, hammering it with instant retries causes a *thundering herd* / *retry storm*, worsening the outage.
- **Backoff Formula:** $T = 2^{\text{attempt}}$ seconds (e.g. 2s, 4s, 8s).

### 2. Timeout Policy (10 seconds)
- Prevents hanging HTTP connections from exhausting ASP.NET thread pool threads.

### 3. Circuit Breaker Policy
- **Rules:** If 3 consecutive requests fail, the circuit **trips open** for 30 seconds.
- **Fail Fast:** Subsequent calls immediately throw `BrokenCircuitException` without wasting network calls or time.
- **Half-Open Probe:** After 30s, the circuit allows a single test request through to check if the AI service recovered.

### 4. Graceful Degradation (HTTP 503)
- The controller catches `BrokenCircuitException` and responds with HTTP 503 and a polite message (*"The AI assistant is temporarily unavailable"*), keeping the rest of the Library API fully operational.
