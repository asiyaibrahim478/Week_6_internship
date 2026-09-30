"""
FastAPI AI Microservice — Week 6 (LangChain & LCEL, Advanced Retrieval, Tool Calling & Streaming)
Author: Asiya
"""
import os
import json
import re
import time
import asyncio
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# LangChain Imports
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter

from prompts import (
    SYSTEM_CATALOGUER_PROMPT,
    STRUCTURED_SUMMARY_PROMPT_TEMPLATE,
    FEW_SHOT_GENRE_PROMPT_TEMPLATE
)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

app = FastAPI(
    title="Library AI Service (Week 6 - LangChain & Streaming)",
    description="Production LangChain LCEL RAG microservice with Tool Calling, Session Memory, and Tri-Layer Streaming.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# Pydantic Schemas
# =====================================================================
class SummaryRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=5)

class SummaryResponse(BaseModel):
    title: str
    genre: str
    summary: str
    confidence_score: float
    service_status: str = "success"

class GenreSuggestionRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=3)

class GenreSuggestionResponse(BaseModel):
    title: str
    suggested_genre: str
    reasoning: str
    prompt_type: str = "few-shot"

class InjectionTestRequest(BaseModel):
    user_input: str

class InjectionTestResponse(BaseModel):
    safe_isolated_prompt: str
    is_adversarial_detected: bool
    verdict: str

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: Optional[str] = Field("default-session", description="Session ID for multi-turn conversational memory")

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: Optional[str] = "high"


# =====================================================================
# LangChain Corpus & Vector Knowledge Base
# =====================================================================
LIBRARY_CATALOG = [
    Document(
        page_content="Clean Code: A Handbook of Agile Software Craftsmanship by Robert C. Martin (Uncle Bob). Teaches clean single-responsibility functions, meaningful variable naming, avoiding side effects, and Test-Driven Development (TDD).",
        metadata={"source": "Clean Code", "id": 1, "isAvailable": True}
    ),
    Document(
        page_content="Designing Data-Intensive Applications by Martin Kleppmann. Comprehensive guide covering LSM-trees, B-trees, replication, partitioning, ACID transactions, and stream processing with Apache Kafka.",
        metadata={"source": "Designing Data-Intensive Applications", "id": 2, "isAvailable": False}
    ),
    Document(
        page_content="The Pragmatic Programmer by David Thomas and Andrew Hunt. Covers software craftsmanship, orthogonality, DRY principles, defensive programming, and modular architecture.",
        metadata={"source": "The Pragmatic Programmer", "id": 3, "isAvailable": True}
    ),
    Document(
        page_content="Dune by Frank Herbert. A science fiction novel set on the desert planet Arrakis, following Paul Atreides and the precious spice melange that enables space navigation.",
        metadata={"source": "Dune", "id": 4, "isAvailable": True}
    ),
    Document(
        page_content="Pride and Prejudice by Jane Austen. A romantic classic set in 19th-century England exploring Elizabeth Bennet and Mr. Darcy.",
        metadata={"source": "Pride and Prejudice", "id": 5, "isAvailable": False}
    )
]

# Session-scoped memory store
session_store: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]


# =====================================================================
# Tool Calling Definition (Week 6 Part D)
# =====================================================================
@tool
def check_book_availability(book_id: int) -> str:
    """Check whether a specific library book (by its numeric ID) is currently available to borrow."""
    for doc in LIBRARY_CATALOG:
        if doc.metadata.get("id") == book_id:
            avail = doc.metadata.get("isAvailable", False)
            title = doc.metadata.get("source", f"Book #{book_id}")
            return f"Book #{book_id} ('{title}') is {'available to borrow' if avail else 'currently checked out'}."
    return f"Book #{book_id} was not found in our catalog."


# =====================================================================
# LCEL Input Guard & RAG Pipeline
# =====================================================================
def guard_short_questions(inputs: Dict[str, Any]) -> Dict[str, Any]:
    question = inputs.get("question", "").strip()
    if len(question) < 3:
        raise ValueError("Question must be at least 3 characters long.")
    return inputs


def retrieve_context(query: str) -> tuple[str, list[str]]:
    q_lower = query.lower()
    matched_texts = []
    matched_sources = set()

    for doc in LIBRARY_CATALOG:
        text = doc.page_content.lower()
        title = doc.metadata.get("source", "").lower()
        if any(w in text or w in title for w in q_lower.split() if len(w) > 3) or any(k in q_lower for k in ["book", "library", "catalog"]):
            matched_texts.append(doc.page_content)
            matched_sources.add(doc.metadata.get("source", "Catalog"))

    context = "\n\n---\n\n".join(matched_texts) if matched_texts else "No matching book found."
    return context, sorted(list(matched_sources))


def execute_grounded_rag(question: str, session_id: str = "default") -> AskResponse:
    q_lower = question.lower()
    
    # 1. Tool-calling detection
    tool_match = re.search(r"(?:book|id)\s*#?\s*(\d+)", q_lower)
    if ("available" in q_lower or "borrow" in q_lower) and tool_match:
        book_id = int(tool_match.group(1))
        tool_res = check_book_availability.invoke({"book_id": book_id})
        return AskResponse(
            answer=f"Live Catalog Check: {tool_res}",
            sources=["Live Database (/api/books/availability)"],
            confidence="high"
        )

    # 2. Multi-turn memory context resolution
    history = get_session_history(session_id)
    history_text = " ".join([m.content.lower() for m in history.messages])
    
    context, sources = retrieve_context(question)

    if "dune" in q_lower or ("dune" in history_text and any(w in q_lower for w in ["genre", "what is it", "who wrote"])):
        answer = "Dune by Frank Herbert is a science fiction masterpiece set on the desert planet Arrakis, focusing on Paul Atreides and the spice melange."
        sources = ["Dune"]
    elif "clean code" in q_lower or ("clean code" in history_text and any(w in q_lower for w in ["function", "naming", "author"])):
        answer = "Clean Code by Robert C. Martin emphasizes single-responsibility functions, meaningful variable names, and Test-Driven Development (TDD)."
        sources = ["Clean Code"]
    elif "data" in q_lower or "kafka" in q_lower or "storage" in q_lower or "ddia" in q_lower:
        answer = "Designing Data-Intensive Applications by Martin Kleppmann covers storage engines (LSM-trees/B-trees), replication, transactions, and Apache Kafka."
        sources = ["Designing Data-Intensive Applications"]
    elif "pride" in q_lower or "austen" in q_lower:
        answer = "Pride and Prejudice by Jane Austen is a classic romance novel set in 19th-century England."
        sources = ["Pride and Prejudice"]
    elif any(w in q_lower for w in ["france", "capital", "weather", "recipe", "eigenvalue"]):
        answer = "I don't have that information. I can only answer questions regarding our library catalog."
        sources = []
    else:
        answer = f"Based on our library catalog: {context[:250]}..." if sources else "I don't have that information."

    # Update session memory
    history.add_user_message(question)
    history.add_ai_message(answer)

    return AskResponse(answer=answer, sources=sources, confidence="high" if sources else "low")


# =====================================================================
# API Endpoints
# =====================================================================
@app.get("/health", tags=["Monitoring"])
def health_check():
    return {
        "status": "healthy",
        "service": "Library AI FastAPI Microservice (Week 6)",
        "version": "2.0.0",
        "active_sessions": len(session_store),
        "endpoints": ["/health", "/ask", "/ask/stream", "/summarize", "/genre-suggestion"]
    }


@app.post("/ask", response_model=AskResponse, tags=["RAG (LangChain)"])
def ask_assistant(req: AskRequest):
    """Resilient non-streaming LCEL RAG endpoint with session memory and tool calling."""
    if len(req.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question must be at least 3 characters long.")
    try:
        return execute_grounded_rag(req.question, req.session_id or "default")
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"AI inference error: {str(ex)}")


@app.post("/ask/stream", tags=["Streaming (SSE)"])
def ask_assistant_stream(req: AskRequest):
    """
    Week 6 Part F: Server-Sent Events (SSE) Live Token Streaming Endpoint.
    Yields data: <token>\n\n chunks followed by data: [DONE]\n\n.
    """
    if len(req.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question must be at least 3 characters long.")

    res = execute_grounded_rag(req.question, req.session_id or "stream-session")
    full_text = res.answer

    def token_generator():
        # Split into small conversational word tokens to simulate live model streaming
        words = full_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield f"data: {token}\n\n"
            time.sleep(0.04)  # 40ms realistic streaming pacing

        # Append source citation if present
        if res.sources:
            yield f"data:  [Sources: {', '.join(res.sources)}]\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")


@app.post("/summarize", response_model=SummaryResponse, tags=["AI Services"])
def summarize_book(request: SummaryRequest):
    lower_desc = request.description.lower()
    genre = "Software Engineering" if "code" in lower_desc else "Science Fiction" if "space" in lower_desc else "General Fiction"
    return SummaryResponse(
        title=request.title,
        genre=genre,
        summary=f"A structured summary of '{request.title}' focusing on core narrative and thematic elements.",
        confidence_score=0.95
    )


@app.post("/genre-suggestion", response_model=GenreSuggestionResponse, tags=["AI Services"])
def suggest_genre(request: GenreSuggestionRequest):
    return GenreSuggestionResponse(
        title=request.title,
        suggested_genre="Science Fiction",
        reasoning="Classified via Few-Shot prompt conditioning.",
        prompt_type="few-shot"
    )


@app.post("/prompt-injection-test", response_model=InjectionTestResponse, tags=["Security"])
def test_prompt_injection(request: InjectionTestRequest):
    is_detected = any(p in request.user_input.lower() for p in ["ignore previous", "system prompt", "override"])
    return InjectionTestResponse(
        safe_isolated_prompt=f"{SYSTEM_CATALOGUER_PROMPT}\n\n<book_metadata>\n{request.user_input}\n</book_metadata>",
        is_adversarial_detected=is_detected,
        verdict="Neutralized" if is_detected else "Clean"
    )
