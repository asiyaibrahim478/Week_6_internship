# 📚 Library Management System & AI Service (Week 6 Milestone)

**Author / Intern:** Asiya  
**Repository:** [`asiyaibrahim478/Week_5_internship`](https://github.com/asiyaibrahim478/Week_5_internship.git)  
**Milestone Version:** `v0.6-week6`

[![Framework: .NET 8](https://img.shields.io/badge/.NET-8.0-512BD4?logo=dotnet&logoColor=white)](https://dotnet.microsoft.com/)
[![Frontend: Angular](https://img.shields.io/badge/Frontend-Angular-DD0031?logo=angular&logoColor=white)](https://angular.dev/)
[![AI Backend: FastAPI & LangChain](https://img.shields.io/badge/AI_Backend-FastAPI_%26_LangChain-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streaming: Server--Sent_Events](https://img.shields.io/badge/Streaming-SSE_(Live)-FF5722?logo=fastapi&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
[![Resilience: Polly](https://img.shields.io/badge/Resilience-Retry_%26_Circuit_Breaker-4CAF50)](https://github.com/App-vNext/Polly)
[![Database: SQL Server & EF Core](https://img.shields.io/badge/Database-SQL_Server_%26_EF_Core-CC292B?logo=microsoftsqlserver&logoColor=white)](https://learn.microsoft.com/en-us/ef/core/)

---

## 🌟 Overview & Week 6 Objectives (LangChain, Tools, Resilience & Streaming)

Week 6 transitions from manual learning exercises to **production-shaped full-stack engineering**, establishing a resilient, streaming, multi-turn AI assistant across all three tiers:
1. **Part A (LangChain Fundamentals & LCEL):** Rebuilding RAG pipelines with composable Runnables (`|`), `RunnablePassthrough`, and `RunnableLambda` input guards.
2. **Part B (Advanced Retrieval & Splitting):** Hierarchical `RecursiveCharacterTextSplitter` and `MultiQueryRetriever` query expansion.
3. **Part C (Structured Output & Memory):** `with_structured_output` (Pydantic schema binding) and session-scoped memory (`RunnableWithMessageHistory`) for multi-turn pronoun resolution.
4. **Part D (Tool Calling):** Equipping the model with `@tool check_book_availability` to query live .NET database availability (`/api/books/{id}/availability`).
5. **Part E (Resilient .NET $\rightarrow$ AI Integration):** Typed `AiServiceClient` with exponential backoff retries, timeout, circuit breaker (`BrokenCircuitException`), and graceful degradation (HTTP 503).
6. **Part F (Tri-Layer End-to-End Streaming):** Real-time Server-Sent Events (SSE) token streaming from FastAPI through the .NET proxy with `Response.Body.FlushAsync()` to the Angular `ReadableStream` Chat UI.
7. **Part G (Git Interactive Rebase):** History cleanup via `git rebase -i` and safe pushing with `--force-with-lease`.

---

## 🔄 End-to-End Streaming Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Client["Frontend SPA (Angular 18)"]
        ChatUI["Chat Assistant Component\n(Token-by-Token Typing Effect)"]
        ChatSvc["ChatService (Native fetch + ReadableStream)"]
    end

    subgraph BackendAPI[".NET 8 Web API (:5000)"]
        AuthMiddleware["JWT Auth Middleware"]
        AsstCtrl["AssistantController (/api/assistant/ask/stream)"]
        ResilientHandler["Resilient Client (Retry & Circuit Breaker)"]
        FlushProxy["StreamReader & Response.Body.FlushAsync()"]
    end

    subgraph AIService["Python FastAPI AI Service (:8000)"]
        FastAPIStream["Streaming Endpoint (/ask/stream)"]
        LCELChain["LangChain LCEL RAG Pipeline"]
        MemStore["Session Memory (ChatMessageHistory)"]
        AvailTool["@tool check_book_availability"]
    end

    subgraph ExternalLLM["LLM Provider (Claude / GPT-4o-mini)"]
        Inference["Grounded Generation & Token Stream"]
    end

    ChatUI -->|1. User Prompt (Session Keyed)| ChatSvc
    ChatSvc -->|2. POST /api/assistant/ask/stream + Bearer JWT| AuthMiddleware
    AuthMiddleware --> AsstCtrl
    AsstCtrl --> ResilientHandler
    ResilientHandler -->|3. Forward Stream Request| FastAPIStream
    FastAPIStream --> LCELChain
    LCELChain <--> MemStore
    LCELChain <--> AvailTool
    LCELChain -->|4. Prompt & Tool Calls| Inference
    Inference -->|5. Token Stream (data: text\n\n)| FastAPIStream
    FastAPIStream -->|6. SSE Chunks| FlushProxy
    FlushProxy -->|7. Live Flushed SSE Stream| ChatSvc
    ChatSvc -->|8. Real-time onChunk Callback| ChatUI
```

> [!WARNING]
> **Known Architecture Limitation:** The session store in `ai-service` currently uses an in-memory dictionary (`dict[str, ChatMessageHistory]`). In a multi-instance production environment, this should be backed by a distributed persistent cache such as **Redis** (`RedisChatMessageHistory`).

---

## 🏗️ Repository Structure

```text
├── LibraryAPI/                       # ASP.NET Core 8 Web API
│   ├── Controllers/                  # AuthController (JWT, Register, Login), BooksController
│   ├── Data/                         # LibraryDbContext (EF Core)
│   ├── DTOs/                         # RegisterDto, LoginDto, AuthResponseDto
│   ├── Models/                       # Book, Author, Category, User
│   ├── Repositories/                 # IBookRepository, BookRepository, InMemoryBookRepository
│   ├── Services/                     # IBookService, BookService
│   ├── appsettings.Development.json  # JWT Secrets (Development)
│   └── Program.cs                    # JWT Auth Scheme, Swagger Bearer, CORS, Pipeline
│
├── library-frontend/                 # Angular 17/18 Standalone Client
│   ├── src/app/
│   │   ├── components/login/         # Reactive Login & Register component
│   │   ├── book-list/                # Book catalog with Admin-conditional actions
│   │   ├── book-form/                # Guarded Book creation form
│   │   ├── services/                 # AuthService (JWT state, signals)
│   │   ├── interceptors/             # Functional authInterceptor
│   │   ├── guards/                   # Functional authGuard
│   │   ├── app.config.ts             # withInterceptors([authInterceptor])
│   │   └── app.routes.ts             # Route configurations with authGuard
│
├── ai-service/                       # FastAPI AI Microservice (Python)
│   ├── main.py                       # FastAPI application & Pydantic endpoints
│   ├── prompts.py                    # Zero-Shot, Few-Shot & Role-based Prompt Templates
│   ├── requirements.txt              # FastAPI, Uvicorn, Pydantic dependencies
│   └── README.md                     # Microservice guide & test curl commands
│
├── Week4_PartA_AuthBackend/          # Part A documentation & test commands
├── Week4_PartB_AngularAuth/          # Part B architecture notes & interceptor design
├── Week4_PartC_FastAPI/              # Part C FastAPI foundations & OpenAPI notes
├── Week4_PartD_LLM/                  # Part D LLM scripts (History, Streaming, JSON)
├── Week4_PartE_PromptEngineering/    # Part E Prompt experiments & injection tests
├── Week4_PartF_GitPractice/          # Part F Merge conflict resolution guide
├── Week4_CheckStage_Answers.md       # Comprehensive check stage questions & answers
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md      # Standardized PR template
└── README.md                         # Project documentation
```

---

## 🚀 How to Run the Applications

### 1. Backend (.NET 8 Web API)
```bash
cd LibraryAPI
dotnet build
dotnet run
```
- **API URL:** `http://localhost:5252`
- **Swagger Documentation:** `http://localhost:5252/swagger` (Use the **Authorize** lock button to supply your Bearer JWT).

### 2. Frontend (Angular Client)
```bash
cd library-frontend
npm install
npm start
```
- **Web UI:** `http://localhost:4200`
- **Demo Accounts:**
  - **Admin User:** `admin` / `Admin123!` (Full permissions + Delete)
  - **Standard User:** `Asiya` / `password123` (View / Add / Edit)

### 3. AI Microservice (FastAPI + Python)
```bash
cd ai-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

---

## 📡 REST API Specifications

### Authentication Endpoints (`LibraryAPI`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Public | Registers a new user with hashed password |
| `POST` | `/api/auth/login` | Public | Validates credentials and returns JWT Bearer token |

### Book Catalog Endpoints (`LibraryAPI`)
| Method | Endpoint | Required Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/books` | Public | Retrieves all books |
| `GET` | `/api/books/{id}` | Public | Retrieves a single book by ID |
| `POST` | `/api/books` | `Bearer JWT` (Any User) | Adds a new book |
| `PUT` | `/api/books/{id}` | `Bearer JWT` (Any User) | Updates an existing book |
| `DELETE` | `/api/books/{id}` | `Bearer JWT` (`Admin` role only) | Removes a book (403 for non-admins) |

### AI Microservice Endpoints (`ai-service`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health probe & service metadata |
| `POST` | `/summarize` | Returns structured JSON summary & genre classification |
| `POST` | `/genre-suggestion` | Few-shot conditioned genre categorization |
| `POST` | `/prompt-injection-test` | Demonstrates defensive input isolation |

---

## 🛡️ Git Workflow & Conventional Commits

Commit history adheres to conventional commit formatting:
- `feat:` Feature implementations (`feature/jwt-auth-backend`, `feature/angular-auth`, `feature/ai-fastapi-service`)
- `fix:` Bug fixes and conflict resolutions
- `docs:` Documentation updates
- `chore:` Configuration and PR templates

**Milestone Release Tag:** `v0.4-week4`
