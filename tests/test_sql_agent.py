import pytest
from fastapi.testclient import TestClient

def test_execute_query(client):
    """
    Test executing a SQL query via the API.
    """
    # Test request data
    request_data = {
        "query": "Find users with id 1",
        "jira_issue_key": "TEST-1",
        "additional_context": "Looking for specific user details"
    }
    
    # Make the request
    response = client.post("/api/sql-agent/query", json=request_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Query executed successfully"
    
    # Check response data structure
    result = data["data"]
    assert "sql" in result
    assert "results" in result
    assert "row_count" in result
    assert "execution_time_ms" in result
    assert "explanation" in result
    
    # Check specific values
    assert result["sql"] == "SELECT * FROM users WHERE id = 1"
    assert result["row_count"] == 1
    assert isinstance(result["results"], list)
    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == 1

def test_explain_query(client):
    """
    Test explaining a SQL query via the API.
    """
    # Test request data
    request_data = {
        "query": "Find users with id 1",
        "jira_issue_key": "TEST-1",
        "additional_context": "Looking for specific user details"
    }
    
    # Make the request
    response = client.post("/api/sql-agent/explain", json=request_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Query explanation generated successfully"
    
    # Check explanation
    assert data["data"] == "This query retrieves the user with ID 1"

def test_execute_query_without_jira(client):
    """
    Test executing a query without Jira context.
    """
    # Test request data
    request_data = {
        "query": "Find all users",
        "jira_issue_key": None,
        "additional_context": None
    }
    
    # Make the request
    response = client.post("/api/sql-agent/query", json=request_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Check result contains SQL and results
    assert "sql" in data["data"]
    assert "results" in data["data"]

def test_execute_query_with_invalid_request(client):
    """
    Test executing a query with an invalid request.
    """
    # Test with empty request
    request_data = {}
    
    # Make the request
    response = client.post("/api/sql-agent/query", json=request_data)
    
    # Check response indicates an error
    assert response.status_code == 422  # Validation error
