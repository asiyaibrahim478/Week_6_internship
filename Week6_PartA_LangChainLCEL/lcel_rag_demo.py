"""
Week 6 Part A — LangChain Fundamentals & LCEL (LangChain Expression Language)

Standardizes RAG components behind common Runnable interfaces composed using the pipe (|) operator.
Features:
1. RunnableSequence (|)
2. RunnablePassthrough
3. RunnableLambda custom input guard (rejecting questions < 3 chars)
4. Data type tracing through every stage of the pipeline
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


# -------------------------------------------------------------
# 1. Custom RunnableLambda: Input Guard
# -------------------------------------------------------------
def guard_short_questions(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates input question length.
    Raises ValueError if question is under 3 characters before invoking expensive LLM/retrieval steps.
    Input Type: dict -> Output Type: dict
    """
    question = inputs.get("question", "").strip()
    if len(question) < 3:
        raise ValueError(f"InputGuard: Question '{question}' is too short (< 3 chars) to answer meaningfully.")
    return inputs


# -------------------------------------------------------------
# 2. Simulated / Real Vector Retriever & Document Formatter
# -------------------------------------------------------------
SAMPLE_DOCS = [
    Document(page_content="Clean Code by Robert C. Martin teaches writing clean functions, meaningful names, and TDD.", metadata={"source": "Clean Code"}),
    Document(page_content="Designing Data-Intensive Applications by Martin Kleppmann covers replication, transactions, and Apache Kafka.", metadata={"source": "DDIA"}),
    Document(page_content="Dune by Frank Herbert is a science fiction novel set on Arrakis involving the spice melange.", metadata={"source": "Dune"}),
]


def mock_retriever(query: str) -> list[Document]:
    """Simulates retriever returning relevant documents."""
    q_lower = query.lower()
    matches = [doc for doc in SAMPLE_DOCS if any(w in doc.page_content.lower() for w in q_lower.split() if len(w) > 3)]
    return matches if matches else SAMPLE_DOCS[:2]


def format_docs(docs: list[Document]) -> str:
    """Formats list of Document objects into a single context string."""
    return "\n\n---\n\n".join(f"[{doc.metadata.get('source', 'Unknown')}] {doc.page_content}" for doc in docs)


# -------------------------------------------------------------
# 3. Model Initializer (Live or Fallback Mock Runnable)
# -------------------------------------------------------------
def get_chat_model():
    if OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        except Exception:
            pass
    if ANTHROPIC_API_KEY:
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.0)
        except Exception:
            pass

    # Deterministic Mock Runnable Model for offline testing
    def mock_model_invoke(prompt_value):
        text = prompt_value.to_string() if hasattr(prompt_value, "to_string") else str(prompt_value)
        q_part = text.split("Question:")[-1].lower() if "Question:" in text else text.lower()
        if "science fiction" in q_part or "dune" in q_part:
            return "Based on the provided context, Dune by Frank Herbert is the science fiction novel set on Arrakis."
        elif "clean code" in q_part or "function" in q_part:
            return "Based on the provided context, Clean Code by Robert C. Martin teaches clean functions and TDD."
        elif "data" in q_part or "kafka" in q_part:
            return "Based on the provided context, Designing Data-Intensive Applications covers replication, transactions, and Kafka."
        else:
            return "I don't have that information."

    return RunnableLambda(mock_model_invoke)


# -------------------------------------------------------------
# 4. Assembling the LCEL Chain
# -------------------------------------------------------------
prompt = ChatPromptTemplate.from_template(
    "Answer using ONLY the context below. If it's not there, say you don't know.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
)

model = get_chat_model()
retriever_runnable = RunnableLambda(lambda x: mock_retriever(x["question"] if isinstance(x, dict) else str(x)))

# LCEL Composition
chain = (
    RunnableLambda(guard_short_questions)
    | {
        "context": retriever_runnable | format_docs,
        "question": RunnablePassthrough(lambda x: x["question"] if isinstance(x, dict) else str(x))
    }
    | prompt
    | model
    | StrOutputParser()
)


# -------------------------------------------------------------
# 5. Execution & Challenge Demonstrations
# -------------------------------------------------------------
def run_lcel_demo():
    print("==================================================================")
    print(" WEEK 6 PART A: LANGCHAIN EXPRESSION LANGUAGE (LCEL) DEMO")
    print("==================================================================")

    # Test 1: Valid query
    q1 = {"question": "Which books are science fiction in the catalog?"}
    print(f"\n[Test 1] Invoking chain with valid query: '{q1['question']}'")
    answer = chain.invoke(q1)
    print(f"Result:\n{answer}")

    # Test 2: Input guard check (Passing 1-character query to verify exception)
    print("\n[Test 2] Testing RunnableLambda Input Guard with invalid 1-char query ('?') ...")
    try:
        chain.invoke({"question": "?"})
        print("[-] FAILED: Guard failed to intercept short question.")
    except ValueError as ve:
        print(f"[+] SUCCESS: Guard intercepted invalid query before LLM call!")
        print(f"    Caught expected exception: {ve}")


if __name__ == "__main__":
    run_lcel_demo()
