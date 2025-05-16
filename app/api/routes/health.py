from fastapi import APIRouter, Depends
from app.db.connection import get_db_connection
from app.schemas.response import ResponseModel
from app.core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncConnection
import time

router = APIRouter()
logger = get_logger(__name__)

@router.get(
    "/health",
    response_model=ResponseModel[dict],
    summary="Health check endpoint",
    description="Returns the health status of the API and its dependencies",
)
async def health_check(
    db_connection: AsyncConnection = Depends(get_db_connection)
):
    start_time = time.time()
    
    # Check database connection
    db_status = "healthy"
    db_message = "Database connection successful"
    try:
        # Execute a simple query to check database connectivity
        result = await db_connection.execute("SELECT 1")
        await result.fetchone()
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
        db_message = f"Database connection error: {str(e)}"
    
    elapsed_time = time.time() - start_time
    
    return ResponseModel[dict](
        success=True,
        data={
            "status": "up",
            "uptime": time.time(),
            "response_time": f"{elapsed_time:.4f}s",
            "dependencies": {
                "database": {
                    "status": db_status,
                    "message": db_message
                }
            }
        },
        message="Health check completed"
    )
