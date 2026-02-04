
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Honeypot"
    MONGODB_URL: str
    DB_NAME: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
