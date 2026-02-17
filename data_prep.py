import pandas as pd
from datasets import load_dataset
import os

def prepare_dataset():
    print("Loading Empathetic Dialogues dataset...")
    try:
        # Using a subset for benchmarking
        dataset = load_dataset("empathetic_dialogues", split="train", streaming=True)
        
        conversations = []
        current_conv = []
        conv_id = None
        
        count = 0
        for item in dataset:
            if item['conv_id'] != conv_id:
                if current_conv:
                    conversations.append(current_conv)
                current_conv = []
                conv_id = item['conv_id']
            
            current_conv.append({
                "role": "user" if item['speaker_idx'] % 2 == 0 else "assistant",
                "content": item['utterance']
            })
            
            if len(conversations) >= 60: # We need 50+ conversations
                break
        
        # Save to raw
        output_path = os.path.join("data", "raw", "conversations.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        import json
        with open(output_path, "w") as f:
            json.dump(conversations, f)
            
        print(f"Dataset prepared with {len(conversations)} conversations at {output_path}")
        
    except Exception as e:
        print(f"Error preparing dataset: {e}")

if __name__ == "__main__":
    prepare_dataset()
