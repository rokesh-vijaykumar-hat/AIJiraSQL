from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from app.services.sql_agent import SQLAgentService
from app.services.jira_service import JiraService
from app.services.openai_service import OpenAIService
from app.db.connection import get_db_connection
from app.db.repository import SQLRepository
from app.config import settings

# OpenAI service
def get_openai_service():
    return OpenAIService(api_key=settings.OPENAI_API_KEY)

# Jira service
def get_jira_service(openai_service: OpenAIService = Depends(get_openai_service)):
    return JiraService(
        jira_url=settings.JIRA_URL,
        jira_user_email=settings.JIRA_USER_EMAIL,
        jira_api_token=settings.JIRA_API_TOKEN,
        openai_service=openai_service
    )

# SQL Repository
def get_sql_repository(db_connection: AsyncConnection = Depends(get_db_connection)):
    return SQLRepository(db_connection=db_connection)

# SQL Agent Service
def get_sql_agent_service(
    sql_repository: SQLRepository = Depends(get_sql_repository),
    jira_service: JiraService = Depends(get_jira_service),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    return SQLAgentService(
        sql_repository=sql_repository,
        jira_service=jira_service,
        openai_service=openai_service
    )
