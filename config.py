import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
    MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "2000"))
