import pytest
from fastapi.testclient import TestClient
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.db.connection import get_db_connection
from app.services.sql_agent import SQLAgentService
from app.services.jira_service import JiraService
from app.services.openai_service import OpenAIService
from app.db.repository import SQLRepository
from app.api.dependencies import get_sql_agent_service, get_jira_service, get_openai_service, get_sql_repository

# Create a test database URL - use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test async engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)

# Create test async session factory
TestSessionLocal = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@pytest.fixture
def client():
    """
    Create a FastAPI TestClient for testing API endpoints.
    """
    # Override the database dependency
    async def override_get_db_connection():
        async with TestSessionLocal() as session:
            yield session.connection()
    
    app.dependency_overrides[get_db_connection] = override_get_db_connection
    
    # Create test client
    return TestClient(app)

@pytest.fixture
def mock_db_connection():
    """
    Create a mock database connection for testing.
    """
    connection = AsyncMock()
    return connection

@pytest.fixture
def mock_sql_repository(mock_db_connection):
    """
    Create a mock SQL repository for testing.
    """
    repository = SQLRepository(mock_db_connection)
    
    # Mock the execute_query method
    async def mock_execute_query(sql):
        if "users" in sql.lower():
            return [
                {"id": 1, "username": "user1", "email": "user1@example.com"},
                {"id": 2, "username": "user2", "email": "user2@example.com"}
            ]
        return []
    
    # Mock the get_schema_info method
    async def mock_get_schema_info():
        return {
            "users": {
                "columns": [
                    {"name": "id", "data_type": "integer", "is_nullable": False, "is_primary_key": True},
                    {"name": "username", "data_type": "varchar", "is_nullable": False, "is_primary_key": False},
                    {"name": "email", "data_type": "varchar", "is_nullable": False, "is_primary_key": False}
                ]
            }
        }
    
    repository.execute_query = mock_execute_query
    repository.get_schema_info = mock_get_schema_info
    
    return repository

@pytest.fixture
def mock_openai_service():
    """
    Create a mock OpenAI service for testing.
    """
    service = AsyncMock(spec=OpenAIService)
    
    # Mock the generate_sql method
    async def mock_generate_sql(prompt):
        return "SELECT * FROM users WHERE id = 1"
    
    # Mock the explain_sql method
    async def mock_explain_sql(natural_language_query, sql_query, jira_context=None):
        return "This query retrieves the user with ID 1"
    
    # Mock the explain_results method
    async def mock_explain_results(query, sql, results, jira_context=None):
        return "The query returned 1 user"
    
    # Mock the extract_context method
    async def mock_extract_context(prompt):
        return "This is a query about users"
    
    service.generate_sql = mock_generate_sql
    service.explain_sql = mock_explain_sql
    service.explain_results = mock_explain_results
    service.extract_context = mock_extract_context
    
    return service

@pytest.fixture
def mock_jira_service(mock_openai_service):
    """
    Create a mock Jira service for testing.
    """
    service = AsyncMock(spec=JiraService)
    
    # Mock the get_issues method
    async def mock_get_issues(project=None, status=None, limit=10):
        return [
            {
                "key": "TEST-1",
                "summary": "Test issue 1",
                "description": "This is a test issue",
                "status": "Open",
                "issue_type": "Bug",
                "created": "2023-01-01T00:00:00.000Z",
                "updated": "2023-01-01T00:00:00.000Z",
                "priority": "High"
            }
        ]
    
    # Mock the get_issue method
    async def mock_get_issue(issue_key):
        return {
            "key": issue_key,
            "summary": f"Test issue {issue_key}",
            "description": "This is a test issue",
            "status": "Open",
            "issue_type": "Bug",
            "created": "2023-01-01T00:00:00.000Z",
            "updated": "2023-01-01T00:00:00.000Z",
            "priority": "High"
        }
    
    # Mock the extract_context method
    async def mock_extract_context(issue_key):
        return f"Context for issue {issue_key}: This is a query about users"
    
    service.get_issues = mock_get_issues
    service.get_issue = mock_get_issue
    service.extract_context = mock_extract_context
    
    return service

@pytest.fixture
def mock_sql_agent_service(mock_sql_repository, mock_jira_service, mock_openai_service):
    """
    Create a mock SQL agent service for testing.
    """
    service = SQLAgentService(
        sql_repository=mock_sql_repository,
        jira_service=mock_jira_service,
        openai_service=mock_openai_service
    )
    
    # Mock the execute_query method
    async def mock_execute_query(natural_language_query, jira_issue_key=None, context=None):
        return {
            "sql": "SELECT * FROM users WHERE id = 1",
            "results": [{"id": 1, "username": "user1", "email": "user1@example.com"}],
            "row_count": 1,
            "execution_time_ms": 10.5,
            "explanation": "The query returned 1 user"
        }
    
    # Mock the explain_query method
    async def mock_explain_query(natural_language_query, jira_issue_key=None, context=None):
        return "This query retrieves the user with ID 1"
    
    # Use patch to replace the methods with our mocks
    service.execute_query = mock_execute_query
    service.explain_query = mock_explain_query
    
    return service

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for testing.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def override_dependencies(mock_sql_agent_service, mock_jira_service, mock_openai_service, mock_sql_repository):
    """
    Override dependencies for testing.
    """
    app.dependency_overrides[get_sql_agent_service] = lambda: mock_sql_agent_service
    app.dependency_overrides[get_jira_service] = lambda: mock_jira_service
    app.dependency_overrides[get_openai_service] = lambda: mock_openai_service
    app.dependency_overrides[get_sql_repository] = lambda: mock_sql_repository
    
    yield
    
    # Clean up
    app.dependency_overrides = {}
