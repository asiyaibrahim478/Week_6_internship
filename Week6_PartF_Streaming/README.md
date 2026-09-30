# Week 6 — Part F: End-to-End Streaming (FastAPI $\rightarrow$ .NET $\rightarrow$ Angular)

## Why Streaming Matters
Instead of making users stare at a loading spinner for 5–10 seconds while the LLM generates a complete response, streaming delivers tokens live as they are generated (*Time-to-First-Token* $< 500\text{ms}$).

---

## 🌊 Tri-Layer Streaming Architecture

```
[ Angular Browser Client ]
       │  1. POST /api/assistant/ask/stream (with Bearer JWT)
       ▼
[ .NET 8 Web API Proxy ]
       │  2. POST /ask/stream (HttpCompletionOption.ResponseHeadersRead)
       ▼
[ FastAPI AI Service ]
       │  3. LLM Token Stream Generator
       ▼
[ .NET StreamReader Loop ]
       │  4. Response.WriteAsync(line) + Response.Body.FlushAsync()
       ▼
[ Angular ReadableStream ]
       │  5. TextDecoder -> onChunk(token) -> Real-time UI render
       ▼
[ Live Chat UI ]
```

---

## ⚠️ Why `FlushAsync()` is Critical
By default, web servers buffer outbound HTTP responses in memory chunks (typically 4KB–8KB) to optimize network packet efficiency. Without explicit `await Response.Body.FlushAsync()` calls after each SSE event line, the .NET proxy buffers all tokens and sends them in one single burst at the end, completely destroying the streaming user experience!

---

## ⚠️ Why Browser Native `fetch()` is Used Over Angular `HttpClient`
Angular's standard `HttpClient` is designed for discrete Request/Response lifecycles (emitting a single RxJS Observable value when `HttpResponse` finishes). Reading an open chunked byte stream requires low-level access to the web standard `ReadableStream` API via native `fetch()` and `response.body.getReader()`.
