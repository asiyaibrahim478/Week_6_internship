# Week 6 — Part C: Structured Output & Conversation Memory

## Key Learnings

### 1. `with_structured_output` vs. Prompt-Only JSON
- Asking an LLM in plain text to *"return JSON"* is non-deterministic and frequently breaks at scale due to markdown wrappers, stray commas, or preamble text.
- `with_structured_output` binds strict JSON schema directly via model tool-calling / grammar constraints, returning strongly-typed Pydantic model instances reliably.

### 2. `RunnableWithMessageHistory` & Session-Scoped Memory
- In enterprise backends, hundreds of users interact simultaneously.
- Conversation state cannot be a global variable; it must be keyed by a distinct `session_id` (e.g. from a user auth token or session header).

### 3. In-Memory vs. Production Storage
- For development and local testing, an in-memory `dict[str, ChatMessageHistory]` is used.
- In production, in-memory dictionaries reset on container/server restarts. Production implementations substitute Redis (`RedisChatMessageHistory`) or database tables (PostgreSQL/SQL Server).

### Running the Demo
```bash
python structured_memory_demo.py
```
