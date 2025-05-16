from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.schemas.jira import JiraIssueResponse, JiraContextRequest
from app.schemas.response import ResponseModel
from app.services.jira_service import JiraService
from app.api.dependencies import get_jira_service
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get(
    "/jira/issues",
    response_model=ResponseModel[List[JiraIssueResponse]],
    summary="Get issues from Jira",
    description="Retrieves a list of issues from Jira based on optional filters",
)
async def get_jira_issues(
    project: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    jira_service: JiraService = Depends(get_jira_service)
):
    logger.info(f"Fetching Jira issues: project={project}, status={status}, limit={limit}")
    try:
        issues = await jira_service.get_issues(project=project, status=status, limit=limit)
        return ResponseModel[List[JiraIssueResponse]](
            success=True,
            data=issues,
            message=f"Retrieved {len(issues)} Jira issues successfully"
        )
    except Exception as e:
        logger.error(f"Error fetching Jira issues: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Jira issues: {str(e)}"
        )

@router.get(
    "/jira/issues/{issue_key}",
    response_model=ResponseModel[JiraIssueResponse],
    summary="Get a specific Jira issue",
    description="Retrieves details for a specific Jira issue by its key",
)
async def get_jira_issue(
    issue_key: str,
    jira_service: JiraService = Depends(get_jira_service)
):
    logger.info(f"Fetching Jira issue: {issue_key}")
    try:
        issue = await jira_service.get_issue(issue_key)
        return ResponseModel[JiraIssueResponse](
            success=True,
            data=issue,
            message=f"Retrieved Jira issue {issue_key} successfully"
        )
    except Exception as e:
        logger.error(f"Error fetching Jira issue {issue_key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Jira issue: {str(e)}"
        )

@router.post(
    "/jira/context",
    response_model=ResponseModel[str],
    summary="Extract context from Jira issue",
    description="Extracts relevant context from a Jira issue for use in SQL queries",
)
async def extract_jira_context(
    request: JiraContextRequest,
    jira_service: JiraService = Depends(get_jira_service)
):
    logger.info(f"Extracting context from Jira issue: {request.issue_key}")
    try:
        context = await jira_service.extract_context(request.issue_key)
        return ResponseModel[str](
            success=True,
            data=context,
            message=f"Context extracted from Jira issue {request.issue_key} successfully"
        )
    except Exception as e:
        logger.error(f"Error extracting context from Jira issue {request.issue_key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting context from Jira issue: {str(e)}"
        )
