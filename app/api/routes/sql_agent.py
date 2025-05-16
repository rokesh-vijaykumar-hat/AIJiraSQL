from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.schemas.sql_agent import SQLQueryRequest, SQLQueryResponse
from app.schemas.response import ResponseModel
from app.services.sql_agent import SQLAgentService
from app.api.dependencies import get_sql_agent_service
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post(
    "/sql-agent/query",
    response_model=ResponseModel[SQLQueryResponse],
    summary="Execute a natural language query using the AI SQL Agent",
    description="Converts a natural language query into SQL and executes it against the database",
)
async def execute_query(
    request: SQLQueryRequest,
    sql_agent_service: SQLAgentService = Depends(get_sql_agent_service)
):
    logger.info(f"Received query request: {request.query}")
    try:
        result = await sql_agent_service.execute_query(
            natural_language_query=request.query,
            jira_issue_key=request.jira_issue_key,
            context=request.additional_context
        )
        return ResponseModel[SQLQueryResponse](
            success=True,
            data=result,
            message="Query executed successfully"
        )
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing query: {str(e)}"
        )

@router.post(
    "/sql-agent/explain",
    response_model=ResponseModel[str],
    summary="Explain the SQL for a natural language query",
    description="Converts a natural language query into SQL and explains it without execution",
)
async def explain_query(
    request: SQLQueryRequest,
    sql_agent_service: SQLAgentService = Depends(get_sql_agent_service)
):
    logger.info(f"Received explain request: {request.query}")
    try:
        explanation = await sql_agent_service.explain_query(
            natural_language_query=request.query,
            jira_issue_key=request.jira_issue_key,
            context=request.additional_context
        )
        return ResponseModel[str](
            success=True,
            data=explanation,
            message="Query explanation generated successfully"
        )
    except Exception as e:
        logger.error(f"Error explaining query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error explaining query: {str(e)}"
        )
