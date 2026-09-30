# Week 6 — Part A: LangChain Fundamentals & LCEL

## Overview
LangChain Expression Language (LCEL) standardizes models, prompts, retrievers, and parsers behind common `Runnable` interfaces composed with the pipe operator (`|`).

---

## 🔍 Data Type Tracing Through the LCEL Chain

```text
[Input: dict {"question": str}]
       │
       ▼
1. RunnableLambda(guard_short_questions) ──────> Returns: dict {"question": str}
       │
       ▼
2. Dict-of-Runnables Parallel Step:
   ├── "context": retriever | format_docs ───────> Returns: str (Formatted context)
   └── "question": RunnablePassthrough() ─────────> Returns: str (Original question)
       │
       ▼ Output of Step 2: dict {"context": str, "question": str}
       │
       ▼
3. ChatPromptTemplate.from_template(...) ────────> Returns: PromptValue / ChatPromptValue
       │
       ▼
4. ChatModel (ChatAnthropic / ChatOpenAI) ───────> Returns: AIMessage
       │
       ▼
5. StrOutputParser() ────────────────────────────> Returns: str (Final text output)
```

---

## 🛡️ Input Guard Verification
Running a question with fewer than 3 characters triggers the `guard_short_questions` `RunnableLambda` immediately, raising a `ValueError` before any downstream token charges or retrieval lookups occur.

### Running the Script
```bash
python lcel_rag_demo.py
```
