"""
Week 6 Project — Interactive Live Streaming Chat Client
Tests multi-turn conversation memory, live streaming, and dynamic tool calls from the terminal.
"""
import sys
import time
import requests

AI_SERVICE_URL = "http://127.0.0.1:8000"


def main():
    print("\n" + "=" * 70)
    print(" 🤖 WELCOME TO WEEK 6 LIBRARY AI ASSISTANT (LIVE STREAMING & MEMORY)")
    print("=" * 70)
    print("Features:")
    print("  • LangChain LCEL RAG & Multi-turn session memory")
    print("  • Live availability tool calling (e.g. 'Is book 4 available?')")
    print("  • Real-time SSE token-by-token streaming")
    print("Type 'reset' to start a new session, or 'exit' to quit.\n")

    session_id = f"cli_user_{int(time.time())}"

    while True:
        try:
            print(f"[Session: {session_id}]")
            user_input = input("💬 You: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye! 👋\n")
                break
            if user_input.lower() == "reset":
                session_id = f"cli_user_{int(time.time())}"
                print(f"\n🔄 Session reset. Started fresh session: {session_id}\n")
                continue

            print("🤖 Assistant: ", end="", flush=True)

            # Stream response via SSE
            resp = requests.post(
                f"{AI_SERVICE_URL}/ask/stream",
                json={"question": user_input, "session_id": session_id},
                stream=True,
                timeout=10
            )

            if resp.status_code != 200:
                print(f"\n[Error: {resp.status_code} - {resp.text}]")
                continue

            for line in resp.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    token = line[5:].strip()
                    if token == "[DONE]":
                        break
                    print(token + " ", end="", flush=True)

            print("\n" + "-" * 70 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋\n")
            sys.exit(0)
        except Exception as ex:
            print(f"\n⚠️ Error connecting to AI Service: {ex}\n")


if __name__ == "__main__":
    main()
