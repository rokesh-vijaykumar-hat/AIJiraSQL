from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SQLQueryRequest(BaseModel):
    """
    Schema for SQL query request.
    """
    query: str = Field(..., description="Natural language query to be converted to SQL")
    jira_issue_key: Optional[str] = Field(None, description="Optional Jira issue key for additional context")
    additional_context: Optional[str] = Field(None, description="Optional additional context for the query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all customers who made purchases over $1000 in the last month",
                "jira_issue_key": "SALES-123",
                "additional_context": "Focus on US customers only"
            }
        }

class SQLQueryResponse(BaseModel):
    """
    Schema for SQL query response.
    """
    sql: str = Field(..., description="The SQL query that was executed")
    results: List[Dict[str, Any]] = Field(..., description="Results of the query")
    row_count: int = Field(..., description="Number of rows returned by the query")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
    explanation: str = Field(..., description="Natural language explanation of the results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT * FROM customers WHERE total_purchases > 1000 AND purchase_date >= CURRENT_DATE - INTERVAL '1 month'",
                "results": [
                    {"id": 1, "name": "John Doe", "total_purchases": 1500.0, "purchase_date": "2023-04-15"}
                ],
                "row_count": 1,
                "execution_time_ms": 42.5,
                "explanation": "The query shows customers who spent over $1000 in the last month. Only 1 customer (John Doe) met this criteria, spending $1500 on April 15, 2023."
            }
        }
