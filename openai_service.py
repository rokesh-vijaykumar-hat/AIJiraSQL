"""
OpenAI integration service for direct interaction with OpenAI models.
"""
"""
AI Agent integration service for SQL generation and result explanation.
"""
import os
import json
import logging
import time
from typing import Dict, Any, List, Optional

import httpx

AI_AGENT_URL = os.getenv("AI_AGENT_URL", "http://ai-agent:8080")

class OpenAIService:
    """
    Service for interaction with internal AI Agent for SQL generation and explanation.
    """
    def __init__(self):
        self.agent_url = AI_AGENT_URL
        self.is_configured = True  # Assuming AI Agent is always available

    async def generate_sql(
        self,
        query: str,
        schema_info: Dict[str, Any],
        jira_context: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate SQL using internal AI Agent.
        """
        try:
            payload = {
                "query": query,
                "schema_info": schema_info,
                "jira_context": jira_context,
                "additional_context": additional_context,
            }

            async with httpx.AsyncClient() as client:
                start_time = time.time()
                response = await client.post(f"{self.agent_url}/generate-sql", json=payload)
                duration = time.time() - start_time

            if response.status_code != 200:
                raise Exception(f"AI Agent returned {response.status_code}: {response.text}")

            result = response.json()
            logging.info(f"SQL generation completed in {duration:.2f} seconds")
            return {
                "sql_query": result.get("sql_query", "-- No SQL returned"),
                "explanation": result.get("explanation", "No explanation provided.")
            }

        except Exception as e:
            logging.error(f"Error calling AI Agent for SQL generation: {e}")
            return {
                "sql_query": f"SELECT * FROM customers LIMIT 10 -- Error fallback for: {query}",
                "explanation": "Fallback SQL query due to error in AI Agent."
            }

    async def explain_results(
        self,
        query: str,
        sql: str,
        results: List[Dict[str, Any]],
        jira_context: Optional[str] = None
    ) -> str:
        """
        Explain SQL results using internal AI Agent.
        """
        try:
            payload = {
                "query": query,
                "sql": sql,
                "results": results,
                "jira_context": jira_context
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.agent_url}/explain-results", json=payload)

            if response.status_code != 200:
                raise Exception(f"AI Agent returned {response.status_code}: {response.text}")

            result = response.json()
            return result.get("explanation", "No explanation provided.")

        except Exception as e:
            logging.error(f"Error calling AI Agent for result explanation: {e}")
            row_count = len(results)
            return f"The query returned {row_count} results based on your request about {query}."
