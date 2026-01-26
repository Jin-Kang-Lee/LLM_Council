"""Configuration settings for the Earnings Analyzer backend."""

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q2_K"

# Agent Configuration
MAX_DISCUSSION_ROUNDS = 3  # Number of back-and-forth exchanges in Phase 3

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
