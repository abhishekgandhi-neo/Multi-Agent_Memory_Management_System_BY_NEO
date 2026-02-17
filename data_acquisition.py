
import os
import json
from datasets import load_dataset

def acquire_dailydialog():
    print("Loading DailyDialog dataset...")
    dataset = load_dataset("daily_dialog", trust_remote_code=True)
    
    processed_conversations = []
    # Take a subset for benchmarking (e.g., 50 conversations to ensure variety and long turns)
    for i in range(min(50, len(dataset["train"]))):
        dialogue = dataset["train"][i]["dialog"]
        processed_conversations.append({
            "conversation_id": f"dailydialog_{i}",
            "turns": dialogue
        })
    
    os.makedirs("./data/raw", exist_ok=True)
    output_path = "./data/raw/conversations.json"
    with open(output_path, "w") as f:
        json.dump(processed_conversations, f, indent=2)
    
    print(f"Saved {len(processed_conversations)} conversations to {output_path}")

if __name__ == "__main__":
    acquire_dailydialog()
