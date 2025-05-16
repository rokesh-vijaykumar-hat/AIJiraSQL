from pydantic import BaseModel, Field, Generic, TypeVar
from typing import Optional, Any

# Define a generic type variable
T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    """
    Generic response model for all API endpoints.
    
    Attributes:
        success: Whether the request was successful
        data: The response data
        message: Optional message
    """
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "Example"},
                "message": "Operation completed successfully"
            }
        }
