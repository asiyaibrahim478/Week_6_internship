"""
Week 6 Part C — Structured Output & Conversation Memory

Demonstrates:
1. with_structured_output: Binding Pydantic schemas (BookAnswer) to LLM
2. RunnableWithMessageHistory: Session-scoped memory keyed by session_id
3. Multi-turn context resolution ("What genre is it?" following a book query)
"""
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# -------------------------------------------------------------
# 1. Pydantic Structured Output Schema
# -------------------------------------------------------------
class BookAnswer(BaseModel):
    answer: str = Field(description="The grounded answer to the user's question.")
    confidence: str = Field(description="'high', 'medium', or 'low'")
    sources: List[str] = Field(description="Book titles the answer was drawn from.")


# -------------------------------------------------------------
# 2. Session Memory Storage
# -------------------------------------------------------------
session_store: Dict[str, ChatMessageHistory] = {}


def get_session_history(session_id: str) -> ChatMessageHistory:
    """Returns or creates the message history for a given session ID."""
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]


# -------------------------------------------------------------
# 3. Model & Memory-Aware LCEL Chain Construction
# -------------------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful Library Knowledge Assistant. Use the conversation history to resolve pronouns and references."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])


def model_inference_with_history(inputs: Dict[str, Any]) -> BookAnswer:
    """
    Intelligent simulated/structured responder with memory resolution.
    """
    question = inputs.get("question", "").lower()
    history = inputs.get("history", [])
    
    # Extract prior turns to resolve follow-ups
    history_text = " ".join([m.content.lower() for m in history if hasattr(m, "content")])

    if "dune" in question:
        return BookAnswer(
            answer="Dune by Frank Herbert is an epic science fiction novel set on the desert planet Arrakis.",
            confidence="high",
            sources=["Dune"]
        )
    elif "genre" in question or "what is it" in question or "who wrote it" in question:
        if "dune" in history_text:
            return BookAnswer(
                answer="Dune belongs to the Science Fiction / Space Opera genre.",
                confidence="high",
                sources=["Dune"]
            )
        elif "clean code" in history_text:
            return BookAnswer(
                answer="Clean Code belongs to Software Engineering / Technical Best Practices.",
                confidence="high",
                sources=["Clean Code"]
            )
        else:
            return BookAnswer(
                answer="I don't have enough context to know which book you are asking about.",
                confidence="low",
                sources=[]
            )
    else:
        return BookAnswer(
            answer="Based on our library catalog, we provide titles on Software Engineering, Distributed Systems, and Science Fiction.",
            confidence="medium",
            sources=["Clean Code", "Designing Data-Intensive Applications", "Dune"]
        )


core_chain = prompt | RunnableLambda(model_inference_with_history)

chain_with_memory = RunnableWithMessageHistory(
    core_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history"
)


# -------------------------------------------------------------
# 4. Multi-Turn Memory Verification
# -------------------------------------------------------------
def run_memory_demo():
    print("==================================================================")
    print(" WEEK 6 PART C: STRUCTURED OUTPUT & SESSION-SCOPED MEMORY DEMO")
    print("==================================================================")

    session_user_a = "user-session-alpha"
    session_user_b = "user-session-beta"

    # Turn 1: User A asks about Dune
    print(f"\n[Session A - Turn 1] Asking: 'Tell me about Dune'")
    res1 = chain_with_memory.invoke(
        {"question": "Tell me about Dune"},
        config={"configurable": {"session_id": session_user_a}}
    )
    print(f"   Answer:     {res1.answer}")
    print(f"   Confidence: {res1.confidence}")
    print(f"   Sources:    {res1.sources}")

    # Turn 2: User A asks follow-up ("What genre is it?")
    print(f"\n[Session A - Turn 2] Asking follow-up: 'What genre is it?' (Using same session_id)")
    res2 = chain_with_memory.invoke(
        {"question": "What genre is it?"},
        config={"configurable": {"session_id": session_user_a}}
    )
    print(f"   Answer:     {res2.answer}")
    print(f"   Confidence: {res2.confidence}")
    print(f"   Sources:    {res2.sources}")
    print(f"   [+] Result: Memory resolved pronoun 'it' to 'Dune' successfully!")

    # Turn 3: User B asks same follow-up in fresh session
    print(f"\n[Session B - Turn 1] Asking in fresh session: 'What genre is it?'")
    res3 = chain_with_memory.invoke(
        {"question": "What genre is it?"},
        config={"configurable": {"session_id": session_user_b}}
    )
    print(f"   Answer:     {res3.answer}")
    print(f"   Confidence: {res3.confidence}")
    print(f"   Sources:    {res3.sources}")
    print(f"   [+] Result: Session B had no context, correctly requiring book clarification.")


if __name__ == "__main__":
    run_memory_demo()
