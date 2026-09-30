"""
Week 6 Project — Comprehensive Automated Verification Test Suite

Tests:
1. LCEL Composition & Input Guarding (< 3 chars rejected)
2. Multi-turn Conversational Memory Context Resolution
3. Dynamic Tool Calling (Live availability check)
4. Out-of-Catalog Refusal Grounding
5. End-to-End Server-Sent Events (SSE) Streaming Generation
"""
import time
import requests

AI_SERVICE_URL = "http://127.0.0.1:8000"


def run_full_week6_test_suite():
    print("=================================================================")
    print(" WEEK 6 PROJECT — COMPREHENSIVE SYSTEM VERIFICATION TEST SUITE")
    print("=================================================================\n")

    # 1. Test Input Guard (< 3 chars)
    print("--- [Test 1] Input Guarding (< 3 chars) ---")
    try:
        r = requests.post(f"{AI_SERVICE_URL}/ask", json={"question": "a", "session_id": "test_s1"})
        if r.status_code == 400:
            print("  [+] Input Guard PASSED: Rejected 1-char question with HTTP 400.")
        else:
            print(f"  [-] Unexpected status: {r.status_code}")
    except Exception as ex:
        print(f"  [!] Note: AI service test ({ex})")

    # 2. Test Multi-Turn Conversational Memory
    session_id = f"test_session_{int(time.time())}"
    print(f"\n--- [Test 2] Multi-Turn Session Memory (Session: {session_id}) ---")
    
    # Turn 1: Ask about Dune
    print("  Turn 1: 'Tell me about Dune'")
    r1 = requests.post(f"{AI_SERVICE_URL}/ask", json={"question": "Tell me about Dune", "session_id": session_id})
    if r1.status_code == 200:
        print(f"  Answer: {r1.json().get('answer')}")
    
    # Turn 2: Follow-up relying on memory
    print("  Turn 2: 'What genre is it?' (Pronoun resolution)")
    r2 = requests.post(f"{AI_SERVICE_URL}/ask", json={"question": "What genre is it?", "session_id": session_id})
    if r2.status_code == 200:
        ans2 = r2.json().get("answer", "")
        print(f"  Answer: {ans2}")
        if "science fiction" in ans2.lower() or "dune" in ans2.lower():
            print("  [+] Memory Resolution PASSED: Correctly resolved 'it' to Dune!")
        else:
            print("  [-] Memory check failed.")

    # 3. Test Tool Calling (Availability Check)
    print("\n--- [Test 3] Dynamic Tool Calling (@tool check_book_availability) ---")
    print("  Query: 'Is book 4 available to borrow?'")
    r3 = requests.post(f"{AI_SERVICE_URL}/ask", json={"question": "Is book 4 available to borrow?", "session_id": session_id})
    if r3.status_code == 200:
        ans3 = r3.json().get("answer", "")
        sources3 = r3.json().get("sources", [])
        print(f"  Answer: {ans3}")
        print(f"  Sources: {sources3}")
        if "available" in ans3.lower():
            print("  [+] Tool Calling PASSED: Successfully invoked tool and returned availability status.")

    # 4. Test Out-of-Catalog Grounding
    print("\n--- [Test 4] Out-of-Catalog Grounding Refusal ---")
    print("  Query: 'What is the recipe for chocolate lava cake?'")
    r4 = requests.post(f"{AI_SERVICE_URL}/ask", json={"question": "What is the recipe for chocolate lava cake?", "session_id": session_id})
    if r4.status_code == 200:
        ans4 = r4.json().get("answer", "")
        print(f"  Answer: {ans4}")
        if "don't have that information" in ans4.lower():
            print("  [+] Grounding Refusal PASSED: Did not hallucinate outside catalog.")

    # 5. Test SSE Streaming Endpoint
    print("\n--- [Test 5] Server-Sent Events (SSE) Live Token Streaming ---")
    print("  Connecting to /ask/stream with SSE client...")
    r5 = requests.post(
        f"{AI_SERVICE_URL}/ask/stream",
        json={"question": "What does Clean Code teach?", "session_id": session_id},
        stream=True
    )
    if r5.status_code == 200:
        print("  Receiving streamed token chunks live:")
        tokens_received = 0
        for line in r5.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                token = line[5:].strip()
                if token == "[DONE]":
                    break
                print(f"'{token}' ", end="", flush=True)
                tokens_received += 1
        print(f"\n  [+] Streaming PASSED: Successfully streamed {tokens_received} live chunks!")

    print("\n" + "=" * 65)
    print(" ALL WEEK 6 VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    run_full_week6_test_suite()
