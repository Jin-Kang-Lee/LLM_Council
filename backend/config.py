"""Configuration settings for the Earnings Analyzer backend."""

import os
from dotenv import load_dotenv

# Load variables from backend/.env (or repo-root .env) into os.environ
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------------------------------------------------------
# Groq API — per-agent key/model groups
# ---------------------------------------------------------------------------
# Agent group 1: Risk Analyst + Deep Research Analyst
GROQ_API_KEY_1 = os.getenv("GROQ_API_KEY_1", "")
GROQ_MODEL_1   = os.getenv("GROQ_MODEL_1", "llama-3.3-70b-versatile")

# Agent group 2: Sentiment Analyst + Master Analyst
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2", "")
GROQ_MODEL_2   = os.getenv("GROQ_MODEL_2", "llama-3.3-70b-versatile")

# Agent group 3: Governance Analyst + Business & Ops Analyst
GROQ_API_KEY_3 = os.getenv("GROQ_API_KEY_3", "")
GROQ_MODEL_3   = os.getenv("GROQ_MODEL_3", "llama-3.3-70b-versatile")

# Groq base URL (OpenAI-compatible)
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ---------------------------------------------------------------------------
# Legacy Ollama configuration
# (kept for rag_faithfulness_llm.py which hasn't been migrated yet)
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1"

# ---------------------------------------------------------------------------
# LlamaCloud (PDF parsing)
# ---------------------------------------------------------------------------
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")

# ---------------------------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------------------------
MAX_DISCUSSION_ROUNDS = 1  # Number of back-and-forth exchanges in Phase 3

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------
API_HOST = "0.0.0.0"
API_PORT = 8000

# ---------------------------------------------------------------------------
# RAG Configuration
# ---------------------------------------------------------------------------
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "vector_db")
REFERENCE_LIB_PATH = os.path.join(os.path.dirname(__file__), "data", "reference_library")
RAG_MAX_QUERY_CHARS  = int(os.getenv("RAG_MAX_QUERY_CHARS", "1600"))
RAG_MIN_QUERY_CHARS  = int(os.getenv("RAG_MIN_QUERY_CHARS", "8"))
RAG_MAX_CHUNKS       = int(os.getenv("RAG_MAX_CHUNKS", "4"))
RAG_FETCH_K          = int(os.getenv("RAG_FETCH_K", "12"))
RAG_MAX_CHUNK_CHARS  = int(os.getenv("RAG_MAX_CHUNK_CHARS", "1800"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "7000"))
_rag_max_distance    = float(os.getenv("RAG_MAX_DISTANCE", "0"))
RAG_MAX_DISTANCE     = _rag_max_distance if _rag_max_distance > 0 else None
RAG_RERANK_ENABLED   = os.getenv("RAG_RERANK_ENABLED", "1") == "1"
RAG_RERANK_MODEL     = os.getenv("RAG_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RAG_RERANK_TOP_K     = int(os.getenv("RAG_RERANK_TOP_K", "12"))
