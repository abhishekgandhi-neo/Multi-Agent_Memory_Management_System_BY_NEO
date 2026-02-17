import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default Model Selection - UPDATED to gpt-4o-mini
DEFAULT_MODEL = "openai/gpt-4o-mini"
SUMMARIZER_MODEL = "openai/gpt-4o-mini"

# Database Paths
SQLITE_DB_PATH = os.path.join("data", "memory.db")
CHROMA_DB_DIR = os.path.join("data", "chroma")

# Memory Management Constants
HOT_CONTEXT_WINDOW = 5  # Recent turns
COLD_CONTEXT_THRESHOLD = 10  # Move to cold storage/summary after this many turns
MAX_TOKENS_PER_CONTEXT = 2000

# Embedding Model (Local)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
