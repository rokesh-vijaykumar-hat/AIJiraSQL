"""
Configuration module for the AI SQL Agent API.
"""
import os
import logging
from dotenv import load_dotenv
dotenv_loaded = load_dotenv()
print("DEBUG: dotenv loaded:", dotenv_loaded)
print("DEBUG: DATABASE_URL after dotenv load:", os.getenv("DATABASE_URL"))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """
    Application configuration class.
    """
    # Application info
    APP_NAME = "AI SQL Agent API"
    APP_VERSION = "1.0.0"
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    
    # Server settings
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    
    # Database settings
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    PGHOST = os.environ.get("PGHOST", "")
    PGDATABASE = os.environ.get("PGDATABASE", "")
    PGPORT = os.environ.get("PGPORT", "")
    PGUSER = os.environ.get("PGUSER", "")
    PGPASSWORD = os.environ.get("PGPASSWORD", "")
    
    # AI settings
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    DEFAULT_MODEL = "gpt-4o"  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
    
    # AI interaction mode
    # Options: "direct" (use OpenAI directly), "agent" (use separate AI agent service)
    AI_INTERACTION_MODE = os.environ.get("AI_INTERACTION_MODE", "agent").lower()
    
    # AI Agent service URL (used when AI_INTERACTION_MODE = "agent")
    AI_AGENT_URL = os.environ.get("AI_AGENT_URL", "http://0.0.0.0:8080")
    
    # Jira settings
    JIRA_URL = os.environ.get("JIRA_URL", "")
    JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
    JIRA_USER_EMAIL = os.environ.get("JIRA_USER_EMAIL", "")
    
    # Security settings
    SESSION_SECRET = os.environ.get("SESSION_SECRET", "default-secret-key-change-in-production")
    
    # Logging settings
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @classmethod
    def is_direct_mode(cls):
        """Check if the application is configured to use OpenAI directly."""
        return cls.AI_INTERACTION_MODE == "direct"
    
    @classmethod
    def is_agent_mode(cls):
        """Check if the application is configured to use the AI agent service."""
        return cls.AI_INTERACTION_MODE == "agent"
    
    @classmethod
    def validate(cls):
        """
        Validate the configuration and log warnings for missing critical settings.
        """
        # Check database configuration
        if not all([cls.PGHOST, cls.PGDATABASE, cls.PGUSER, cls.PGPASSWORD]):
            logger.warning("Database connection not fully configured. Some functionality will use mock data.")
        
        # Check AI configuration
        if cls.is_direct_mode() and not cls.OPENAI_API_KEY:
            logger.warning("Direct OpenAI mode selected but OPENAI_API_KEY not provided. AI functionality will not work.")
        
        if cls.is_agent_mode() and not cls.AI_AGENT_URL:
            logger.warning("Agent mode selected but AI_AGENT_URL not provided. AI functionality will not work.")
        
        # Check Jira configuration
        if not all([cls.JIRA_URL, cls.JIRA_USER_EMAIL, cls.JIRA_API_TOKEN]):
            logger.warning("Jira integration not fully configured. Jira functionality will be limited.")

# Validate configuration on module import
Config.validate()
logger.info(f"Loaded DB URL: {Config.DATABASE_URL}")
print(f"PGPORT is: {os.getenv('PGPORT')}")
print("DEBUG ENV DATABASE_URL:", os.getenv("DATABASE_URL"))
print("Working directory:", os.getcwd())
