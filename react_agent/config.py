"""
Configuration for ReACT Agent
"""

import os

# Ollama Configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "https://ollama.com")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "9a430fe5f9734565876d821bb4b94212.H_q8zjKAtq0xMC7KAfqnWNsc")

# Agent Configuration
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "10"))
VERBOSE = os.environ.get("VERBOSE", "true").lower() == "true"

# Database Configuration (inherited from bank_db)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+mysqldb://root:root@localhost:3306/bankdb"
)
