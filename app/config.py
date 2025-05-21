from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # This tells Pydantic to load from `.env` file automatically
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application settings
    APP_NAME: str = "AI SQL Agent API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Database settings
    DATABASE_URL: str
    PGHOST: str = ""
    PGDATABASE: str = ""
    PGPORT: str = "5432"
    PGUSER: str = ""
    PGPASSWORD: str = ""
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    DEFAULT_MODEL: str = "gpt-4o"
    
    # Jira settings
    JIRA_URL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_USER_EMAIL: str = ""
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

settings = Settings()
