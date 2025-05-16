from typing import Optional, Dict, Any, List
import json

from app.db.repository import SQLRepository
from app.services.jira_service import JiraService
from app.services.openai_service import OpenAIService
from app.schemas.sql_agent import SQLQueryResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

class SQLAgentService:
    """
    Service for executing SQL queries using AI agent capabilities.
    """
    def __init__(
        self,
        sql_repository: SQLRepository,
        jira_service: JiraService,
        openai_service: OpenAIService
    ):
        self.sql_repository = sql_repository
        self.jira_service = jira_service
        self.openai_service = openai_service
        logger.info("SQLAgentService initialized")
        
    async def _get_schema_info(self) -> str:
        """
        Get database schema information for the LLM context.
        
        Returns:
            String representation of the database schema
        """
        try:
            schema_info = await self.sql_repository.get_schema_info()
            return json.dumps(schema_info)
        except Exception as e:
            logger.error(f"Error fetching schema info: {str(e)}")
            raise
    
    async def _get_jira_context(self, jira_issue_key: Optional[str]) -> Optional[str]:
        """
        Get context from a Jira issue if a key is provided.
        
        Args:
            jira_issue_key: Optional Jira issue key
            
        Returns:
            Context extracted from the Jira issue, or None if no key provided
        """
        if not jira_issue_key:
            return None
            
        try:
            return await self.jira_service.extract_context(jira_issue_key)
        except Exception as e:
            logger.warning(f"Could not extract context from Jira issue {jira_issue_key}: {str(e)}")
            return None
    
    async def _generate_sql(
        self,
        natural_language_query: str,
        schema_info: str,
        jira_context: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Generate SQL from a natural language query using OpenAI.
        
        Args:
            natural_language_query: The natural language query
            schema_info: Database schema information
            jira_context: Optional context from a Jira issue
            additional_context: Optional additional context
            
        Returns:
            Generated SQL query
        """
        prompt = self._build_sql_prompt(
            natural_language_query, 
            schema_info, 
            jira_context, 
            additional_context
        )
        
        sql_query = await self.openai_service.generate_sql(prompt)
        logger.info(f"Generated SQL: {sql_query}")
        return sql_query
    
    def _build_sql_prompt(
        self,
        natural_language_query: str,
        schema_info: str,
        jira_context: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build a prompt for the SQL generation task.
        
        Args:
            natural_language_query: The natural language query
            schema_info: Database schema information
            jira_context: Optional context from a Jira issue
            additional_context: Optional additional context
            
        Returns:
            Formatted prompt for the OpenAI API
        """
        # Base prompt with schema information
        prompt = f"""
        You are an AI SQL agent that converts natural language queries into SQL.
        
        DATABASE SCHEMA:
        {schema_info}
        
        USER QUERY:
        {natural_language_query}
        """
        
        # Add Jira context if available
        if jira_context:
            prompt += f"""
            
            JIRA CONTEXT:
            {jira_context}
            """
        
        # Add additional context if available
        if additional_context:
            prompt += f"""
            
            ADDITIONAL CONTEXT:
            {additional_context}
            """
            
        # Instructions for output format
        prompt += """
        
        Generate a valid SQL query that addresses the user's request.
        Only return the SQL query without any explanations or comments.
        Ensure the query is optimized and follows best practices.
        """
        
        return prompt
    
    async def execute_query(
        self,
        natural_language_query: str,
        jira_issue_key: Optional[str] = None,
        context: Optional[str] = None
    ) -> SQLQueryResponse:
        """
        Execute a natural language query by converting it to SQL and running it.
        
        Args:
            natural_language_query: The natural language query
            jira_issue_key: Optional Jira issue key for additional context
            context: Optional additional context
            
        Returns:
            Query results and metadata
        """
        logger.info(f"Processing query: '{natural_language_query}', Jira issue: {jira_issue_key}")
        
        # Get schema information and Jira context
        schema_info = await self._get_schema_info()
        jira_context = await self._get_jira_context(jira_issue_key)
        
        # Generate SQL from natural language
        sql_query = await self._generate_sql(
            natural_language_query=natural_language_query,
            schema_info=schema_info,
            jira_context=jira_context,
            additional_context=context
        )
        
        # Execute the SQL query
        start_time = __import__('time').time()
        results = await self.sql_repository.execute_query(sql_query)
        execution_time = __import__('time').time() - start_time
        
        # Generate an explanation for the results
        explanation = await self.openai_service.explain_results(
            query=natural_language_query,
            sql=sql_query,
            results=results[:5] if results else [],  # Sample of results for explanation
            jira_context=jira_context
        )
        
        logger.info(f"Query executed successfully, returned {len(results) if results else 0} rows")
        
        return SQLQueryResponse(
            sql=sql_query,
            results=results,
            row_count=len(results) if results else 0,
            execution_time_ms=round(execution_time * 1000, 2),
            explanation=explanation
        )
    
    async def explain_query(
        self,
        natural_language_query: str,
        jira_issue_key: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Explain the SQL for a natural language query without executing it.
        
        Args:
            natural_language_query: The natural language query
            jira_issue_key: Optional Jira issue key for additional context
            context: Optional additional context
            
        Returns:
            SQL query with explanation
        """
        logger.info(f"Explaining query: '{natural_language_query}', Jira issue: {jira_issue_key}")
        
        # Get schema information and Jira context
        schema_info = await self._get_schema_info()
        jira_context = await self._get_jira_context(jira_issue_key)
        
        # Generate SQL from natural language
        sql_query = await self._generate_sql(
            natural_language_query=natural_language_query,
            schema_info=schema_info,
            jira_context=jira_context,
            additional_context=context
        )
        
        # Generate detailed explanation
        explanation = await self.openai_service.explain_sql(
            natural_language_query=natural_language_query,
            sql_query=sql_query,
            jira_context=jira_context
        )
        
        return explanation
