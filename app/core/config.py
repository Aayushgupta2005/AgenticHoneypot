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

# Create a single instance to import elsewhere
settings = Settings()