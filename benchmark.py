import os
import json
import time
import argparse
import pandas as pd
from openrouter_client import OpenRouterClient
from database import DatabaseManager
from memory_system import MemoryAgentSystem

def benchmark():
    parser = argparse.ArgumentParser()
    parser.add_argument("--convs", type=int, default=3, help="Number of conversations to test")
    parser.add_argument("--turns", type=int, default=15, help="Max turns per conversation")
    parser.add_argument("--real-api", action="store_true", help="Use real OpenRouter API")
    parser.add_argument("--threshold", type=float, default=0.3, help="Efficiency threshold (0.3 = 30%)")
    args = parser.parse_args()

    # Load dataset
    conversations_path = os.path.join("data", "raw", "conversations.json")
    if not os.path.exists(conversations_path):
        print("Dataset not found. Please run data_prep.py first.")
        return

    with open(conversations_path, "r") as f:
        conversations = json.load(f)

    # Filter for conversations with enough turns to demonstrate savings
    conversations = [c for c in conversations if len(c) >= 5][:args.convs]
    results = []
    
    db = DatabaseManager()
    api_key = os.getenv("OPENROUTER_API_KEY") if args.real_api else "sk-or-v1-dummy"
    client = OpenRouterClient(api_key=api_key)
    system = MemoryAgentSystem(db, client, verbose=True)
    
    print("\n" + "="*80)
    print("RUNNING OPTIMIZED CONTEXT MANAGEMENT BENCHMARK")
    print("Targeting gpt-4o-mini with Competitive Pruning")
    print("="*80)
    
    for i, conv in enumerate(conversations):
        session_id = f"sess_bench_{i}_{int(time.time())}"
        print(f"\n[CONVERSATION {i+1}/{len(conversations)}]")
        
        baseline_cumulative_tokens = 0
        agent_cumulative_tokens = 0
        
        history = []
        turn_data = []
        
        # Reset client usage for fresh conv session
        client.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        for turn_idx, turn in enumerate(conv[:args.turns]):
            if turn['role'] == 'user':
                user_input = turn['content']
                
                # 1. Baseline Token Calculation (Native History Windowing/Full History)
                # Baseline sends all history turns (common for non-agent standard LLM chatbots)
                baseline_payload = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ] + history + [{"role": "user", "content": user_input}]
                
                # 1 token per 4 chars + 4 tokens per msg overhead
                turn_baseline_tokens = (len(json.dumps(baseline_payload)) // 4) + (len(baseline_payload) * 4)
                baseline_cumulative_tokens += turn_baseline_tokens
                
                # 2. Agent System Execution (with Hierarchical Memory)
                print(f"\n--- TURN {turn_idx+1} ---")
                start_time = time.time()
                response = system.generate_response(session_id, user_input)
                latency = (time.time() - start_time) * 1000
                
                # 3. Track Agent Tokens Used for this turn
                current_agent_total = client.token_usage['total_tokens']
                turn_agent_tokens = current_agent_total - agent_cumulative_tokens
                agent_cumulative_tokens = current_agent_total
                
                # 4. Record turn metrics
                savings = (turn_baseline_tokens - turn_agent_tokens) / turn_baseline_tokens if turn_baseline_tokens > 0 else 0
                
                print(f"  > METRICS: Baseline {turn_baseline_tokens} | Agent {turn_agent_tokens} | Turn Saving: {savings:.1%}")
                
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": response or "..."})
                
                turn_data.append({
                    "turn": turn_idx,
                    "baseline": turn_baseline_tokens,
                    "agent": turn_agent_tokens,
                    "latency": latency,
                    "savings": savings
                })
        
        if not turn_data: continue

        avg_lat = sum(t['latency'] for t in turn_data) / len(turn_data)
        total_conv_savings = (baseline_cumulative_tokens - agent_cumulative_tokens) / baseline_cumulative_tokens if baseline_cumulative_tokens > 0 else 0
        
        status = "PASS" if total_conv_savings >= args.threshold else "FAIL"
        
        results.append({
            "conv_id": i,
            "baseline_total": baseline_cumulative_tokens,
            "agent_total": agent_cumulative_tokens,
            "avg_latency": avg_lat,
            "total_savings": total_conv_savings,
            "status": status
        })
        
        print(f"\n>> Conv {i+1} Summary: Saved {total_conv_savings:.1%} (Target: {args.threshold:.0%}) | [{status}]")

    df = pd.DataFrame(results)
    os.makedirs("analysis", exist_ok=True)
    df.to_csv("analysis/benchmark_results.csv", index=False)
    
    mean_savings = df['total_savings'].mean()
    mean_latency = df['avg_latency'].mean()
    success_rate = (df['status'] == 'PASS').mean()
    
    print("\n" + "="*80)
    print(f"OVERALL PERFORMANCE SUMMARY:")
    print(f"- Mean Token Savings: {mean_savings:.2%}")
    print(f"- Mean Retrieval Latency: {mean_latency:.2f} ms")
    print(f"- Efficiency Target Success Rate: {success_rate:.1%}")
    print("="*80)
    
    if mean_savings < args.threshold:
        print(f"WARNING: Overall savings ({mean_savings:.1%}) below target threshold ({args.threshold:.1%})")
    else:
        print(f"SUCCESS: System exceeded the {args.threshold*100}% token efficiency threshold.")

if __name__ == "__main__":
    benchmark()
