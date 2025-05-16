from typing import List, Optional, Dict, Any
import aiohttp
import json
import base64

from app.schemas.jira import JiraIssueResponse
from app.services.openai_service import OpenAIService
from app.core.logging import get_logger

logger = get_logger(__name__)

class JiraService:
    """
    Service for interacting with Jira API and extracting context from issues.
    """
    def __init__(
        self,
        jira_url: str,
        jira_user_email: str,
        jira_api_token: str,
        openai_service: OpenAIService
    ):
        self.jira_url = jira_url.rstrip('/')
        self.jira_user_email = jira_user_email
        self.jira_api_token = jira_api_token
        self.openai_service = openai_service
        
        # Base64 encoded credentials for Basic Auth
        credentials = f"{jira_user_email}:{jira_api_token}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()
        
        logger.info(f"JiraService initialized with URL: {jira_url}")
        
    async def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Jira API.
        
        Args:
            endpoint: The API endpoint (without the base URL)
            method: HTTP method (GET, POST, etc.)
            data: Optional data for POST/PUT requests
            
        Returns:
            JSON response from the API
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.jira_url}{endpoint}"
        headers = {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            logger.debug(f"Making {method} request to {url}")
            
            if method == 'GET':
                async with session.get(url, headers=headers) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"Jira API error ({response.status}): {error_text}")
                        raise Exception(f"Jira API error: {response.status} - {error_text}")
                    return await response.json()
            elif method == 'POST':
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"Jira API error ({response.status}): {error_text}")
                        raise Exception(f"Jira API error: {response.status} - {error_text}")
                    return await response.json()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
    
    async def get_issues(
        self,
        project: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[JiraIssueResponse]:
        """
        Get a list of Jira issues based on filters.
        
        Args:
            project: Optional project key
            status: Optional issue status
            limit: Maximum number of issues to return
            
        Returns:
            List of Jira issues
        """
        # Build JQL query
        jql_parts = []
        if project:
            jql_parts.append(f"project = {project}")
        if status:
            jql_parts.append(f"status = '{status}'")
        
        jql = " AND ".join(jql_parts) if jql_parts else ""
        
        # Make request to search API
        endpoint = f"/rest/api/3/search?jql={jql}&maxResults={limit}"
        response = await self._make_request(endpoint)
        
        # Transform response to schema
        issues = []
        for issue_data in response.get("issues", []):
            issue = JiraIssueResponse(
                key=issue_data.get("key"),
                summary=issue_data.get("fields", {}).get("summary", ""),
                description=issue_data.get("fields", {}).get("description", ""),
                status=issue_data.get("fields", {}).get("status", {}).get("name", ""),
                issue_type=issue_data.get("fields", {}).get("issuetype", {}).get("name", ""),
                created=issue_data.get("fields", {}).get("created", ""),
                updated=issue_data.get("fields", {}).get("updated", ""),
                priority=issue_data.get("fields", {}).get("priority", {}).get("name", "")
            )
            issues.append(issue)
        
        logger.info(f"Retrieved {len(issues)} issues from Jira")
        return issues
    
    async def get_issue(self, issue_key: str) -> JiraIssueResponse:
        """
        Get details for a specific Jira issue.
        
        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            
        Returns:
            Jira issue details
            
        Raises:
            Exception: If the issue cannot be found
        """
        endpoint = f"/rest/api/3/issue/{issue_key}"
        issue_data = await self._make_request(endpoint)
        
        issue = JiraIssueResponse(
            key=issue_data.get("key"),
            summary=issue_data.get("fields", {}).get("summary", ""),
            description=issue_data.get("fields", {}).get("description", ""),
            status=issue_data.get("fields", {}).get("status", {}).get("name", ""),
            issue_type=issue_data.get("fields", {}).get("issuetype", {}).get("name", ""),
            created=issue_data.get("fields", {}).get("created", ""),
            updated=issue_data.get("fields", {}).get("updated", ""),
            priority=issue_data.get("fields", {}).get("priority", {}).get("name", "")
        )
        
        logger.info(f"Retrieved issue {issue_key} from Jira")
        return issue
    
    async def extract_context(self, issue_key: str) -> str:
        """
        Extract relevant context from a Jira issue for SQL queries.
        
        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            
        Returns:
            Extracted context as a string
            
        Raises:
            Exception: If the issue cannot be found or context extraction fails
        """
        # Get the issue details
        issue = await self.get_issue(issue_key)
        
        # Extract context using the OpenAI service
        prompt = f"""
        Extract relevant context for a database query from this Jira issue:
        
        Issue Key: {issue.key}
        Summary: {issue.summary}
        Description: {issue.description}
        Type: {issue.issue_type}
        Status: {issue.status}
        Priority: {issue.priority}
        
        Focus on extracting:
        1. Key requirements or data needs mentioned in the issue
        2. Any specific filters, conditions, or constraints for the query
        3. Time periods or date ranges mentioned
        4. Specific metrics or calculations needed
        5. Any mentioned tables, fields, or data entities
        
        Return only the extracted context in a concise format, focusing on information that would be useful for constructing a SQL query.
        """
        
        context = await self.openai_service.extract_context(prompt)
        logger.info(f"Extracted context from issue {issue_key}")
        
        return context
