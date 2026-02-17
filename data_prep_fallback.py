import json
import os

def generate_long_conversations(count=50, turns_per_conv=25):
    conversations = []
    
    topics = ["space exploration", "AI ethics", "quantum computing", "climate change", "manga", "cooking", "travel", "philosophy"]
    
    for i in range(count):
        topic = topics[i % len(topics)]
        conv = []
        for j in range(turns_per_conv):
            role = "user" if j % 2 == 0 else "assistant"
            if role == "user":
                content = f"Question {j//2 + 1} about {topic}: What are your thoughts on {topic} part {j//2}?"
            else:
                content = f"Response {j//2 + 1}: {topic} is a broad field with many aspects. Here is a detailed thought on part {j//2}..."
            
            conv.append({"role": role, "content": content})
        conversations.append(conv)
        
    output_path = os.path.join("data", "raw", "conversations.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(conversations, f)
    
    print(f"Generated {count} long conversations ({turns_per_conv} turns each) at {output_path}")

if __name__ == "__main__":
    generate_long_conversations()
