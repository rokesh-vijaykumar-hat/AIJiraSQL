import pytest
from fastapi.testclient import TestClient

def test_get_jira_issues(client):
    """
    Test retrieving Jira issues.
    """
    # Make the request
    response = client.get("/api/jira/issues?project=TEST&status=Open&limit=10")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Retrieved" in data["message"]
    
    # Check issues data
    issues = data["data"]
    assert isinstance(issues, list)
    assert len(issues) > 0
    
    # Check issue structure
    issue = issues[0]
    assert "key" in issue
    assert "summary" in issue
    assert "status" in issue

def test_get_jira_issue(client):
    """
    Test retrieving a specific Jira issue.
    """
    # Make the request
    response = client.get("/api/jira/issues/TEST-1")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Retrieved Jira issue TEST-1 successfully" in data["message"]
    
    # Check issue data
    issue = data["data"]
    assert issue["key"] == "TEST-1"
    assert "summary" in issue
    assert "description" in issue
    assert "status" in issue

def test_extract_jira_context(client):
    """
    Test extracting context from a Jira issue.
    """
    # Test request data
    request_data = {
        "issue_key": "TEST-1"
    }
    
    # Make the request
    response = client.post("/api/jira/context", json=request_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Context extracted from Jira issue TEST-1 successfully" in data["message"]
    
    # Check extracted context
    context = data["data"]
    assert "Context for issue TEST-1" in context

def test_get_nonexistent_jira_issue(client, monkeypatch):
    """
    Test error handling when a Jira issue doesn't exist.
    """
    # Mock the get_jira_service dependency to raise an exception
    from app.api.dependencies import get_jira_service
    
    async def mock_get_issue(issue_key):
        raise Exception("Issue not found")
    
    # Get the mock jira service and modify its behavior
    jira_service = get_jira_service()
    jira_service.get_issue = mock_get_issue
    
    # Make the request
    response = client.get("/api/jira/issues/NONEXISTENT-1")
    
    # Check response indicates an error
    assert response.status_code == 500
    data = response.json()
    assert "Error fetching Jira issue" in data["detail"]
