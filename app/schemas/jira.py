from pydantic import BaseModel, Field
from typing import Optional

class JiraIssueResponse(BaseModel):
    """
    Schema for Jira issue response.
    """
    key: str = Field(..., description="Jira issue key (e.g., PROJECT-123)")
    summary: str = Field(..., description="Issue summary")
    description: Optional[str] = Field(None, description="Issue description")
    status: str = Field(..., description="Current status")
    issue_type: str = Field(..., description="Issue type (e.g., Bug, Story)")
    created: str = Field(..., description="Creation date")
    updated: str = Field(..., description="Last update date")
    priority: Optional[str] = Field(None, description="Issue priority")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "SALES-123",
                "summary": "Analyze high-value customers",
                "description": "We need a report of all customers who have made purchases over $1000 in the last 3 months.",
                "status": "Open",
                "issue_type": "Task",
                "created": "2023-04-01T10:00:00.000Z",
                "updated": "2023-04-02T14:30:00.000Z",
                "priority": "High"
            }
        }

class JiraContextRequest(BaseModel):
    """
    Schema for Jira context extraction request.
    """
    issue_key: str = Field(..., description="Jira issue key to extract context from")
    
    class Config:
        json_schema_extra = {
            "example": {
                "issue_key": "SALES-123"
            }
        }
