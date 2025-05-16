from typing import Dict, Any, List, Optional
import json
import os
from openai import OpenAI

from app.core.logging import get_logger

logger = get_logger(__name__)

class OpenAIService:
    """
    Service for interacting with OpenAI API for various natural language tasks.
    """
    def __init__(self, api_key: str):
        # Initialize the OpenAI client
        self.client = OpenAI(api_key=api_key)
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        logger.info(f"OpenAIService initialized with model: {self.model}")
    
    async def generate_sql(self, prompt: str) -> str:
        """
        Generate SQL from a natural language prompt.
        
        Args:
            prompt: The prompt describing the SQL query needed
            
        Returns:
            Generated SQL query
            
        Raises:
            Exception: If SQL generation fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL developer. Generate only the SQL query without explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more deterministic outputs
                max_tokens=1000
            )
            
            sql = response.choices[0].message.content
            # Clean up the SQL (remove markdown code blocks if present)
            sql = sql.replace("```sql", "").replace("```", "").strip()
            
            return sql
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    async def explain_sql(self, natural_language_query: str, sql_query: str, jira_context: Optional[str] = None) -> str:
        """
        Generate an explanation for the SQL query based on the natural language query.
        
        Args:
            natural_language_query: The original natural language query
            sql_query: The generated SQL query
            jira_context: Optional context from a Jira issue
            
        Returns:
            Explanation of the SQL query
        """
        prompt = f"""
        The user asked: "{natural_language_query}"
        
        The following SQL query was generated:
        ```sql
        {sql_query}
        