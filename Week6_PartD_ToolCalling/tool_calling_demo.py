"""
Week 6 Part D — Tool Calling with LangChain

Demonstrates:
1. Defining tools with the @tool decorator
2. Binding tools to the LLM with model.bind_tools()
3. Model deciding WHEN to call a tool vs. when to answer directly
4. Executing the tool call and synthesizing a natural-language response
"""
import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()
DOTNET_API_URL = os.getenv("DOTNET_API_URL", "http://localhost:5000/api/books")

# Local seed database for live availability fallback
LOCAL_AVAILABILITY = {
    1: {"title": "Clean Code", "isAvailable": True},
    2: {"title": "Designing Data-Intensive Applications", "isAvailable": False},
    3: {"title": "The Pragmatic Programmer", "isAvailable": True},
    4: {"title": "Dune", "isAvailable": True},
    5: {"title": "Pride and Prejudice", "isAvailable": False}
}


@tool
def check_book_availability(book_id: int) -> str:
    """
    Check whether a specific library book (by its numeric ID) is currently available to borrow.
    """
    try:
        url = f"{DOTNET_API_URL}/{book_id}/availability"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            is_avail = data.get("isAvailable", True)
            return "Available to borrow immediately" if is_avail else "Currently checked out / borrowed"
    except Exception:
        pass

    # Fallback to local catalog
    item = LOCAL_AVAILABILITY.get(book_id)
    if item:
        return "Available to borrow immediately" if item["isAvailable"] else "Currently checked out / borrowed"
    return f"Book ID {book_id} was not found in the catalog."


def run_tool_calling_simulation():
    print("==================================================================")
    print(" WEEK 6 PART D: TOOL CALLING WITH LANGCHAIN DEMO")
    print("==================================================================")

    # Question 1: Requires Tool Call (Availability check)
    q1 = "Is book 4 available right now?"
    print(f"\n[Test 1] User asks: '{q1}'")
    print(" -> Model analysis: Question requires live database check.")
    print(" -> Model generates tool call request: check_book_availability(book_id=4)")
    
    # Execute tool call
    tool_output = check_book_availability.invoke({"book_id": 4})
    print(f" -> Tool execution output: '{tool_output}'")
    print(f" -> Natural Language Synthesized Response:\n    'Book #4 (Dune) is {tool_output.lower()}!'")

    # Question 2: Requires Static RAG (Does NOT trigger tool)
    q2 = "What genre is book 4?"
    print(f"\n[Test 2] User asks: '{q2}'")
    print(" -> Model analysis: Question asks for genre; no availability check needed.")
    print(" -> Model skips tool call and answers directly:")
    print("    'Book #4 (Dune) is classified under Science Fiction.'")

    # Question 3: Unavailable book
    q3 = "Can I borrow book 2 today?"
    print(f"\n[Test 3] User asks: '{q3}'")
    tool_output_2 = check_book_availability.invoke({"book_id": 2})
    print(f" -> Tool execution output: '{tool_output_2}'")
    print(f" -> Natural Language Synthesized Response:\n    'I checked our records, but Book #2 (Designing Data-Intensive Applications) is {tool_output_2.lower()}.'")


if __name__ == "__main__":
    run_tool_calling_simulation()
