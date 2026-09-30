# Week 6 — Check Stage Questions & Answers

**Candidate / Intern:** Asiya  
**Program:** AI Software Development Internship (.NET + Angular + AI)  
**Week 6:** LangChain & LCEL • Advanced Retrieval • Tool Calling • Resilient .NET $\rightarrow$ AI Integration • End-to-End Streaming • Git Rebase

---

### 1. What is a Runnable, and what does the `|` operator actually do in LCEL?
**Answer:**  
A **Runnable** is a standardized LangChain protocol/interface that defines a common contract (including `.invoke()`, `.stream()`, `.batch()`, and async equivalents) across all components (prompts, chat models, output parsers, retrievers, or custom lambdas).  
The **`|` (pipe) operator** creates a `RunnableSequence`, chaining two runnables such that the output of the left runnable is automatically transformed and piped as the direct input to the right runnable (e.g. `prompt | model | StrOutputParser()`), eliminating manual glue code.

---

### 2. What is `RunnablePassthrough` for, and when do you need it?
**Answer:**  
`RunnablePassthrough` is a special Runnable that takes the incoming input and passes it forward completely unchanged. It is needed in branching/parallel dictionary steps where a later stage needs both a transformed value and the raw original input simultaneously — for example, passing the retrieved formatted context to the prompt while preserving the original user question:
```python
{"context": retriever | format_docs, "question": RunnablePassthrough()}
```

---

### 3. Why can a single retrieval query miss relevant chunks, and how does `MultiQueryRetriever` address that — and what does it cost you in return?
**Answer:**  
- **Why single queries miss chunks:** User questions may use synonyms, phrasing, or idioms that embed at a distance from the exact vocabulary used in the source documents, leading to low cosine similarity.
- **How MultiQueryRetriever fixes it:** It prompts an LLM to generate multiple (e.g. 3) reformulated variations of the original question from different perspectives, retrieves top chunks for each variation, and unions/deduplicates the results.
- **The cost:** Increases latency and cost because it requires an extra upstream LLM call before executing retrieval, and can occasionally introduce noisy/irrelevant chunks on narrow queries.

---

### 4. Why is `with_structured_output` more reliable than asking the model to "return JSON" in plain English?
**Answer:**  
Plain-text prompting for JSON often fails because models may output markdown code fences (```json), conversational conversational preambles ("Here is your JSON:"), trailing commas, or invalid syntax under complex prompts.  
`with_structured_output` binds a Pydantic schema directly to the model's native Tool Calling / JSON Schema API or grammar-constrained sampling, guaranteeing deterministic, type-safe, and validated objects without manual `json.loads` parsing.

---

### 5. Why must conversation memory be keyed by a session ID in a real service?
**Answer:**  
In a multi-user web application or microservice, dozens or thousands of users interact with the backend concurrently. If memory were global or tied to a single instance, conversations would bleed across different users. Keying message histories by a `session_id` isolates each user's multi-turn dialogue history into its own scoped container.

---

### 6. How does tool calling differ from your code directly calling a function?
**Answer:**  
- **Direct function call:** The developer writes explicit procedural code dictating exactly when, where, and with what arguments a function runs.
- **Tool Calling:** The model inspects the user's intent against registered tool definitions (`@tool`), autonomously decides *whether* a tool is necessary, chooses which tool to invoke, and extracts the required argument values into a tool-call request. The application executes the requested tool and feeds the result back to the model for natural language synthesis.

---

### 7. What problem does a retry policy solve, and why does exponential backoff matter instead of retrying instantly?
**Answer:**  
- **Problem solved:** Recovers from transient network glitches, socket blips, or momentary server reloads without failing the user request.
- **Why exponential backoff ($2^{\text{attempt}}$) matters:** If a downstream service is struggling under heavy CPU load or traffic spikes, retrying immediately floods the service with a "retry storm" (thundering herd), driving it into complete failure. Exponential backoff introduces progressively larger pauses, giving the struggling service time to recover.

---

### 8. What does a circuit breaker protect, and what does it cost the user when it's open?
**Answer:**  
- **What it protects:** Protects your own API from resource exhaustion (thread pool starvation, open socket exhaustion, and slow timeouts) when a downstream microservice is down.
- **What it costs the user:** When the circuit is **open**, user requests immediately receive a fast, graceful HTTP 503 response ("Service Temporarily Unavailable") rather than hanging for 15–30 seconds waiting on doomed requests.

---

### 9. Why can't Angular just call the FastAPI streaming endpoint directly instead of going through .NET?
**Answer:**  
1. **Security & Authentication:** The Angular client authenticates with the .NET backend using JWTs and role claims. The internal AI microservice does not manage user identities and should never be exposed publicly to the internet.
2. **Architecture Separation:** The .NET backend acts as the secure API Gateway/Orchestrator enforcing rate limits, logging, audit trails, and business logic before routing requests to internal AI services.

---

### 10. Why did removing `FlushAsync()` break the streaming proxy?
**Answer:**  
Web servers (including Kestrel in ASP.NET Core) buffer outbound response streams in internal memory buffers (typically 4KB–8KB) to optimize TCP packet transmission. Without calling `await Response.Body.FlushAsync()` after each chunk, the server holds all tokens in memory and sends them all at once when the request finishes, turning a live streaming user experience into a delayed bulk response.

---

### 11. What does interactive rebase let you do that a normal commit history doesn't, and why is it dangerous on a shared branch like main?
**Answer:**  
- **What it lets you do:** `git rebase -i` lets you rewrite, reorder, squash multiple WIP/typo commits into clean atomic commits, and standardize commit messages before merging a PR.
- **Why it is dangerous on main:** Rebase modifies commit SHA hashes. Rebasing a shared public branch causes other developers' local copies to diverge, forcing painful conflict resolution and corrupting shared repository history.

---

## 🎯 Suggested Mentor Review — Preparation & Talking Points

### 1. Live 5-Hop Request Flow Walkthrough
- **Hop 1 (Angular):** User types query $\rightarrow$ `ChatService.askStream()` opens native `fetch()` connection to `.NET`.
- **Hop 2 (.NET API):** `AssistantController.AskStream()` receives request, authenticates JWT, and proxies upstream call to FastAPI using `SendAsync(..., ResponseHeadersRead)`.
- **Hop 3 (FastAPI):** `/ask/stream` endpoint invokes LangChain LCEL chain with session memory and `@tool` binding.
- **Hop 4 (LangChain & LLM):** Model generates tokens or executes tool, yielding `data: <token>\n\n` SSE lines.
- **Hop 5 (.NET to Angular):** `.NET` reads stream line-by-line, writes to `Response`, calls `FlushAsync()`, and Angular `ReadableStream` renders tokens live on screen!

### 2. Live Circuit Breaker Demonstration
- Stop the FastAPI microservice.
- Send a question from Angular $\rightarrow$ `.NET` retries 3 times $\rightarrow$ circuit breaker opens $\rightarrow$ subsequent clicks immediately return a fast HTTP 503 banner with zero delay.

### 3. Tool Calling Live Inspection
- Ask *"Is book 4 available?"* $\rightarrow$ Model autonomously triggers `check_book_availability(book_id=4)`.
- Ask *"What genre is book 4?"* $\rightarrow$ Model answers directly from knowledge base without triggering the availability tool.

### 4. Interactive Rebase Demonstration
- Show `git log --oneline` on the feature branch demonstrating a clean, squashed commit history before PR opening.

### 5. Scaling to 1,000 Concurrent Users
- Replace the in-memory `dict[str, ChatMessageHistory]` with distributed **Redis** (`RedisChatMessageHistory`), ensuring session state persists across multiple load-balanced FastAPI instances and survives server restarts.
