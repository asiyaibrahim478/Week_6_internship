# Week 6 — Part D: Tool Calling with LangChain

## Key Concepts

### 1. What is Tool Calling?
Instead of forcing the LLM to guess dynamic or live real-time states (e.g., live book availability, weather, stock prices), **tool calling** equips the model with Python functions decorated with `@tool`.

### 2. How the Decision Loop Works
```text
User Question: "Is book 4 available?"
      │
      ▼
LLM inspects question & bound tools
      │
      ├─► Determines live status is needed
      ▼
LLM emits tool call request: `{"name": "check_book_availability", "args": {"book_id": 4}}`
      │
      ▼
Python executes `check_book_availability.invoke(args)`
      │
      ▼
Tool output returned to LLM
      │
      ▼
LLM synthesizes natural language response for user:
"Book #4 (Dune) is available to borrow immediately!"
```

### 3. Difference from Full Agents (Week 7)
- **Week 6 (Tool Calling):** Single-step tool execution (Decide $\rightarrow$ Call $\rightarrow$ Respond).
- **Week 7 (Autonomous Agents / LangGraph):** Multi-step reasoning loops (Plan $\rightarrow$ Tool 1 $\rightarrow$ Inspect $\rightarrow$ Tool 2 $\rightarrow$ Error Recovery $\rightarrow$ Respond).

### Running the Demo
```bash
python tool_calling_demo.py
```
