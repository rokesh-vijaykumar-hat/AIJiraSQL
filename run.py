"""
Entry point for running the FastAPI application.
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    # Run the FastAPI application with Uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1
    )
