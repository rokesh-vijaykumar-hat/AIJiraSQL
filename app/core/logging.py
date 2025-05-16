import logging
import sys
import json
from datetime import datetime
from typing import Optional

from app.config import settings

class JsonFormatter(logging.Formatter):
    """
    Formatter for JSON-structured logs.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, 'request_id'):
            log_record["request_id"] = record.request_id
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging():
    """
    Configure the logging system based on application settings.
    """
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers to avoid duplicates when reloading
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatting in production, standard formatting in development
    if settings.DEBUG:
        formatter = logging.Formatter(settings.LOG_FORMAT)
    else:
        formatter = JsonFormatter()
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Disable propagation to the root logger
    logger.propagate = False
    
    logger.info(f"Logging initialized with level {settings.LOG_LEVEL}")
    return logger

def get_logger(name: Optional[str] = None):
    """
    Get a logger instance for the given name.
    
    Args:
        name: The name for the logger, usually __name__
        
    Returns:
        A configured logger instance
    """
    if name:
        return logging.getLogger(f"app.{name}")
    return logging.getLogger("app")
