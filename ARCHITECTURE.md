# Agent-Based LLM Memory Management System

## Overview
This system implements a hierarchical memory management architecture for LLMs, utilizing a multi-agent approach and a SQLite + ChromaDB backend. It optimizes context window usage by consolidating older parts of conversations into summaries and using vector-based retrieval for relevant historical context.

## System Architecture

### 1. Agents
- **Storage Agent**: Manages persistence of raw conversation turns in SQLite and embeddings in ChromaDB.
- **Consolidation Agent**: Periodically summarizes older turns once the session exceeds defined thresholds (e.g., 10 messages).
- **Retrieval Agent**: Implements a three-tier retrieval strategy:
    - **Hot Context**: Most recent N turns (defined in `config.py`).
    - **Summarized Context**: The latest consolidated summary for the session.
    - **Relevant Context**: Semantic search results from vector storage.

### 2. Database Schema
#### SQLite (memory.db)
- **sessions**: Tracks unique conversation IDs and metadata.
- **messages**: Stores every turn (role, content, timestamp, token counts, and type).
    - `type`: 'original', 'summary', or 'cold'.
- **metrics**: Stores performance data like latency and token usage per session.

#### ChromaDB (Vector Store)
- Stores embeddings of 'original' messages to enable semantic retrieval.
- **Embedding Method**: Uses a lightweight `HashingVectorizer` from scikit-learn to avoid `torch` dependencies and maintain <100ms latency.

### 3. OpenRouter Integration
- All LLM calls (Completions and Summarizations) pass through a unified `OpenRouterClient`.
- Supports token tracking and error handling.
- Mock mode included for development/testing without active API keys.

## Performance Analysis
- **Latency**: ~80ms (Target: <100ms)
- **Token Efficiency**: Designed for 30-50% savings in long-running conversations (Prunes full history in favor of summary + hot context).

## Installation & Usage
1. `python -m venv venv`
2. `.\venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `python smoke_test.py`
5. `python benchmark.py`
