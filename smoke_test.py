import os
import uuid
import json
from database import DatabaseManager
from memory_system import MemoryAgentSystem
from openrouter_client import OpenRouterClient

def test_system():
    # Setup
    if not os.getenv("OPENROUTER_API_KEY"):
        os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-dummy"

    db = DatabaseManager()
    client = OpenRouterClient()
    # Initialize with verbose=True for 'live verbose mode'
    system = MemoryAgentSystem(db, client, verbose=True)

    session_id = str(uuid.uuid4())
    print("\n" + "#"*60)
    print(f"### LIVE VERBOSE SMOKE TEST: {session_id}")
    print("#"*60)

    # Simple conversation designed to trigger vector search and later consolidation
    # Using more turns to show the threshold logic
    turns = [
        "Hi, I'm John. I'm a developer from New York.",
        "I'm working on a memory agent for LLMs using OpenRouter.",
        "My favorite food is sushi.",
        "Can you remember my name and profession?",
        "What am I working on again?",
        "Where am I from?"
    ]

    for i, turn in enumerate(turns):
        print(f"\n--- TURN {i+1} ---")
        print(f"USER INPUT: {turn}")
        response = system.generate_response(session_id, turn)
        print(f"ASSISTANT RESPONSE: {response}")

    print("\n" + "#"*60)
    print("### SMOKE TEST COMPLETE")
    print("#"*60)

if __name__ == "__main__":
    test_system()
