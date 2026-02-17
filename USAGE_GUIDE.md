# Usage Guide: LLM Memory Manager

## Prerequisites
- Python 3.11+
- OpenRouter API Key (optional, mock mode provided)

## Setup
1. **Initialize Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   Create a `.env` file or export the variable:
   ```bash
   set OPENROUTER_API_KEY=your_key_here
   ```
   *If no key is provided, the system defaults to **Mock Mode** for demonstration.*

## Running the System

### 1. Smoke Test
Verify the end-to-end flow with a simple 3-turn test:
```bash
python smoke_test.py
```

### 2. Benchmarking
Run the comparative study across 50 simulated long conversations:
```bash
python benchmark.py
```
Outputs will be generated in the `analysis/` directory.

### 3. Data Preparation
Regenerate conversations if needed:
```bash
python data_prep_fallback.py
```

## System Components
- `memory_system.py`: The core Agent logic.
- `database.py`: SQLite and ChromaDB integration.
- `openrouter_client.py`: Unified API client with token tracking.
- `config.py`: Global settings (thresholds, models, paths).
