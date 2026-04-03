"""Configuration settings for the Earnings Analyzer backend."""

import os

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q2_K"

# Agent Configuration
MAX_DISCUSSION_ROUNDS = 3  # Number of back-and-forth exchanges in Phase 3

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# RAG Configuration
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "vector_db")
REFERENCE_LIB_PATH = os.path.join(os.path.dirname(__file__), "data", "reference_library")
RAG_MAX_QUERY_CHARS = int(os.getenv("RAG_MAX_QUERY_CHARS", "1600"))
RAG_MIN_QUERY_CHARS = int(os.getenv("RAG_MIN_QUERY_CHARS", "8"))
RAG_MAX_CHUNKS = int(os.getenv("RAG_MAX_CHUNKS", "4"))
RAG_FETCH_K = int(os.getenv("RAG_FETCH_K", "12"))
RAG_MAX_CHUNK_CHARS = int(os.getenv("RAG_MAX_CHUNK_CHARS", "1800"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "7000"))
_rag_max_distance = float(os.getenv("RAG_MAX_DISTANCE", "0"))
RAG_MAX_DISTANCE = _rag_max_distance if _rag_max_distance > 0 else None
RAG_RERANK_ENABLED = os.getenv("RAG_RERANK_ENABLED", "1") == "1"
RAG_RERANK_MODEL = os.getenv("RAG_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RAG_RERANK_TOP_K = int(os.getenv("RAG_RERANK_TOP_K", "12"))
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
