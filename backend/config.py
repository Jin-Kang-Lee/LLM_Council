"""Configuration settings for the Earnings Analyzer backend."""

import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Keys + Models - one pair per specialist agent
GROQ_API_KEY_1 = os.getenv("GROQ_API_KEY_1", "")
GROQ_MODEL_1   = os.getenv("GROQ_MODEL_1", "llama-3.3-70b-versatile")

GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2", "")
GROQ_MODEL_2   = os.getenv("GROQ_MODEL_2", "llama-3.3-70b-versatile")

GROQ_API_KEY_3 = os.getenv("GROQ_API_KEY_3", "")
GROQ_MODEL_3   = os.getenv("GROQ_MODEL_3", "llama-3.3-70b-versatile")

# Agent Configuration
MAX_DISCUSSION_ROUNDS = 3  # Number of back-and-forth exchanges in Phase 3

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
