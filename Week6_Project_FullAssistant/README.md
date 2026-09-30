# Week 6 Project — Library AI Assistant (Fully Wired)

## Overview
Connects the entire stack into a production-grade, resilient, multi-turn AI assistant with tool calling and live token streaming.

---

## 🔄 End-to-End Tri-Layer Architecture

```
[ Angular Chat UI (:4200) ]
       │  1. Native fetch() -> POST /api/assistant/ask/stream (Bearer JWT)
       ▼
[ .NET 8 Web API (:5000) ]
       │  2. Resilient Polly Proxy -> POST /ask/stream
       ▼
[ FastAPI AI Service (:8000) ]
       │  3. LangChain LCEL Pipeline:
       │     • RunnableLambda (Input Guard >= 3 chars)
       │     • Session Memory (ChatMessageHistory)
       │     • @tool check_book_availability
       │     • RecursiveCharacterTextSplitter & MultiQuery
       ▼
[ Live LLM Token Generator ]
       │  4. Server-Sent Events: data: <token>\n\n
       ▼
[ .NET Response.Body.FlushAsync() ]
       │  5. Live Stream Forwarding
       ▼
[ Angular UI ] ──> Token-by-token real-time render
```

---

## 🛠️ Key Components
1. **LangChain LCEL & Memory:** Multi-turn conversational context with pronoun resolution.
2. **Tool Calling:** Automatically checks live book availability from the database when requested.
3. **Resilience & Circuit Breaker:** Exponential backoff retries and graceful HTTP 503 fallback when the downstream AI service fails.
4. **End-to-End SSE Streaming:** Smooth, low-latency live token rendering across all 3 tiers.

---

## 🧪 Testing the System

### 1. Automated Verification Suite
```bash
python test_week6_suite.py
```

### 2. Interactive Terminal Streaming Chat
```bash
python interactive_client.py
```
