import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

class Settings:
    PROJECT_NAME: str = "Agentic Honeypot"
    VERSION: str = "1.0.0"
    
    # API Config
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Database Config
    MONGO_URI: str = os.getenv("MONGO_URI")
    DB_NAME: str = os.getenv("DB_NAME", "honeypot_db")
    
    # Security / Keys
    GUVI_API_KEY: str = os.getenv("GUVI_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    
    # Segmented Key Pools (Comma separated)
    GROQ_KEYS_GLOBAL: str = os.getenv("GROQ_KEYS_GLOBAL") or GROQ_API_KEY # Fallback to single key
    GROQ_KEYS_SCAM: str = os.getenv("GROQ_KEYS_SCAM")
    GROQ_KEYS_GEN: str = os.getenv("GROQ_KEYS_GEN")
    GROQ_KEYS_SAFE: str = os.getenv("GROQ_KEYS_SAFE")
    GROQ_KEYS_EXTRACTION: str = os.getenv("GROQ_KEYS_EXTRACTION")
    HG_KEY1: str = os.getenv("HG_KEY1")
    HG_KEY2: str = os.getenv("HG_KEY2")
    HG_KEY1: str = os.getenv("HG_KEY1")
    HG_KEY2: str = os.getenv("HG_KEY2")
# Create a single instance to import elsewhere
settings = Settings()