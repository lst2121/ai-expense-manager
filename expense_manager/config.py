# expense_manager/config.py

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# LLM Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.0

# CSV File Path
CSV_FILE_PATH = "data/sample_expense.csv"

# Vector Store (for future agentic use)
VECTOR_DB_PATH = "vectorstore/expenses_db"

# Debug mode for LLMChain
DEBUG_MODE = True  # ✅ Add this
