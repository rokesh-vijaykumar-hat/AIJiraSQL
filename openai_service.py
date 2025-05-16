"""
OpenAI integration service for direct interaction with OpenAI models.
"""
import os
import json
import logging
import time
from typing import Dict, Any, List, Optional

# Check if OpenAI API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.warning("OPENAI_API_KEY environment variable not set. Direct OpenAI functionality will not work.")

try:
    from openai import OpenAI
    
    # Initialize OpenAI client if API key is available
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except ImportError:
    logging.warning("OpenAI Python package not installed. Direct OpenAI functionality will not work.")
    openai_client = None

class OpenAIService:
    """
    Service for direct interaction with OpenAI models.
    """
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.client = openai_client
        self.is_configured = bool(self.api_key and self.client)
        
        if not self.is_configured:
            logging.warning("OpenAI service not configured with valid API key.")
    
    async def generate_sql(self, query: str, schema_info: Dict[str, Any], jira_context: Optional[str] = None,
                          additional_context: Optional[str] = None) -> Dict[str, str]:
        """
        Generate SQL from natural language using OpenAI's GPT-4o model.
        
        Args:
            query: Natural language query
            schema_info: Database schema information
            jira_context: Additional context from Jira issue (optional)
            additional_context: Any other context provided by user (optional)
            
        Returns:
            Dictionary containing generated SQL query and explanation
            
        Raises:
            Exception: If generation fails
        """
        if not self.is_configured:
            raise ValueError("OpenAI service is not configured with a valid API key")
        
        try:
            # Create prompt with schema info and context
            schema_str = json.dumps(schema_info, indent=2)
            prompt = f"""You are an AI SQL expert. Given the following database schema:
            
{schema_str}

Your task is to convert this natural language query into a valid SQL query:
"{query}"

"""
            # Add Jira context if available
            if jira_context:
                prompt += f"\nAdditional context from Jira ticket:\n{jira_context}\n"
            
            # Add any additional context
            if additional_context:
                prompt += f"\nAdditional context provided by user:\n{additional_context}\n"
            
            # Add final instructions
            prompt += """
Please provide:
1. The SQL query that would answer this question
2. A brief explanation of what the query does

Format your response as a JSON object with keys 'sql_query' and 'explanation'.
"""
            
            # Make request to OpenAI
            start_time = time.time()
            response = self.client.chat.completions.create(
                model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            end_time = time.time()
            
            # Parse response
            content = response.choices[0].message.content
            if content is not None and isinstance(content, str):
                result = json.loads(content)
                
                logging.info(f"Query generation time: {end_time - start_time:.2f} seconds")
                return {
                    "sql_query": result["sql_query"],
                    "explanation": result["explanation"]
                }
            else:
                raise ValueError("Empty or invalid response from OpenAI API")
        
        except Exception as e:
            logging.error(f"Error generating SQL with OpenAI: {str(e)}")
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    async def explain_results(self, query: str, sql: str, results: List[Dict[str, Any]], 
                             jira_context: Optional[str] = None) -> str:
        """
        Explain SQL query results in natural language using OpenAI's GPT-4o model.
        
        Args:
            query: Original natural language query
            sql: SQL query that was executed
            results: Query results as a list of dictionaries
            jira_context: Additional context from Jira issue (optional)
            
        Returns:
            Natural language explanation of the results
            
        Raises:
            Exception: If explanation fails
        """
        if not self.is_configured:
            raise ValueError("OpenAI service is not configured with a valid API key")
        
        try:
            results_str = json.dumps(results, indent=2)
            prompt = f"""You are an AI SQL expert. Given the following:

Original Query: "{query}"

SQL Query: "{sql}"

Query Results:
{results_str}

Please provide a clear, concise explanation of these results in natural language that would help a business user understand what the data shows. 
Focus on key insights and patterns in the data if applicable.
"""

            if jira_context:
                prompt += f"\nAdditional context from Jira ticket:\n{jira_context}\n"
            
            # Make request to OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[{"role": "user", "content": prompt}]
            )
            
            explanation = response.choices[0].message.content
            
            return explanation if explanation else "Could not generate an explanation."
        
        except Exception as e:
            logging.error(f"Error explaining results with OpenAI: {str(e)}")
            raise Exception(f"Failed to explain results: {str(e)}")