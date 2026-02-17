
import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_visualizations():
    results_path = "analysis/benchmark_results.csv"
    if not os.path.exists(results_path):
        print(f"Results file {results_path} not found.")
        return

    df = pd.read_csv(results_path)
    os.makedirs("analysis", exist_ok=True)

    # 1. Token Comparison (Baseline vs Agent)
    plt.figure(figsize=(10, 6))
    x = range(len(df))
    plt.bar(x, df['baseline_total'], width=0.4, label='Baseline Tokens', align='center')
    plt.bar(x, df['agent_total'], width=0.4, label='Agent System Tokens', align='edge')
    plt.xlabel('Conversation ID')
    plt.ylabel('Total Tokens')
    plt.title('Baseline vs Agent System Token Usage (openai/gpt-4o-mini)')
    plt.legend()
    plt.savefig('analysis/token_comparison.png')
    plt.close()

    # 2. Latency Distribution
    plt.figure(figsize=(10, 6))
    plt.hist(df['avg_latency'], bins=10, color='skyblue', edgecolor='black')
    plt.axvline(df['avg_latency'].mean(), color='red', linestyle='dashed', linewidth=1, label=f'Mean: {df["avg_latency"].mean():.2f}ms')
    plt.xlabel('Average Latency (ms)')
    plt.ylabel('Frequency')
    plt.title('Retrieval Latency Distribution (Agent System)')
    plt.legend()
    plt.savefig('analysis/latency_distribution.png')
    plt.close()

    print("Visualizations generated: token_comparison.png, latency_distribution.png")

if __name__ == "__main__":
    generate_visualizations()
