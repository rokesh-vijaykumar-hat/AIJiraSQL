import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "AI SQL Agent API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")  # Always bind to 0.0.0.0
    PORT: int = int(os.getenv("PORT", "8000"))  # Backend port is 8000
    
    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    PGHOST: str = os.getenv("PGHOST", "")
    PGDATABASE: str = os.getenv("PGDATABASE", "")
    PGPORT: str = os.getenv("PGPORT", "5432")
    PGUSER: str = os.getenv("PGUSER", "")
    PGPASSWORD: str = os.getenv("PGPASSWORD", "")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = "gpt-4o"  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
    
    # Jira settings
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_USER_EMAIL: str = os.getenv("JIRA_USER_EMAIL", "")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

settings = Settings()
