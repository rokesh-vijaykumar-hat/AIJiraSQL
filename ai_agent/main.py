from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for OpenAI API key
use_mock_service = False
if not os.environ.get("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY environment variable not set. Using mock AI service for local testing.")
    use_mock_service = True
    from mock_service import MockAIService
    ai_service = MockAIService()
else:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    except ImportError:
        logger.error("OpenAI package not installed. Install with 'pip install openai'")
        use_mock_service = True
        from mock_service import MockAIService
        ai_service = MockAIService()

app = FastAPI(title="AI SQL Agent Service")

class NLQueryRequest(BaseModel):
    query: str
    jira_context: Optional[str] = None
    schema_info: Dict[str, Any]
    additional_context: Optional[str] = None

class SQLResponse(BaseModel):
    sql_query: str
    explanation: str

@app.get("/")
async def root():
    return {"status": "up", "message": "AI SQL Agent Service is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate-sql", response_model=SQLResponse)
async def generate_sql(request: NLQueryRequest):
    """
    Generate SQL from natural language using OpenAI's GPT-4o model or mock service.
    """
    try:
        if use_mock_service:
            # Use the mock service
            logger.info(f"Using mock service to generate SQL for query: {request.query}")
            result = ai_service.generate_sql(
                request.query, 
                request.schema_info, 
                request.jira_context, 
                request.additional_context
            )
            
            return SQLResponse(
                sql_query=result["sql_query"],
                explanation=result["explanation"]
            )
        else:
            # Use OpenAI
            if not os.environ.get("OPENAI_API_KEY"):
                raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
            # Create prompt with schema info and context
            schema_str = json.dumps(request.schema_info, indent=2)
            prompt = f"""You are an AI SQL expert. Given the following database schema:
            
{schema_str}

Your task is to convert this natural language query into a valid SQL query:
"{request.query}"

"""
            # Add Jira context if available
            if request.jira_context:
                prompt += f"\nAdditional context from Jira ticket:\n{request.jira_context}\n"
            
            # Add any additional context
            if request.additional_context:
                prompt += f"\nAdditional context provided by user:\n{request.additional_context}\n"
            
            # Add final instructions
            prompt += """
Please provide:
1. The SQL query that would answer this question
2. A brief explanation of what the query does

Format your response as a JSON object with keys 'sql_query' and 'explanation'.
"""
            
            # Make request to OpenAI
            start_time = time.time()
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            end_time = time.time()
            
            # Parse response
            content = response.choices[0].message.content
            # Ensure content is a string before parsing as JSON
            if content is not None and isinstance(content, str):
                result = json.loads(content)
                
                logger.info(f"Query generation time: {end_time - start_time:.2f} seconds")
                return SQLResponse(
                    sql_query=result["sql_query"],
                    explanation=result["explanation"]
                )
            else:
                raise HTTPException(status_code=500, detail="Empty or invalid response from OpenAI API")
    
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(e)}")

@app.post("/explain-results")
async def explain_results(
    query: str,
    sql: str,
    results: List[Dict[str, Any]],
    jira_context: Optional[str] = None
):
    """
    Explain SQL query results in natural language using OpenAI's GPT-4o model or mock service.
    """
    try:
        if use_mock_service:
            # Use the mock service
            logger.info(f"Using mock service to explain results for query: {query}")
            explanation = ai_service.explain_results(query, sql, results, jira_context)
            return {"explanation": explanation}
        else:
            # Use OpenAI
            if not os.environ.get("OPENAI_API_KEY"):
                raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
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
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[{"role": "user", "content": prompt}]
            )
            
            explanation = response.choices[0].message.content
            
            return {"explanation": explanation}
    
    except Exception as e:
        logger.error(f"Error explaining results: {e}")
        raise HTTPException(status_code=500, detail=f"Error explaining results: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)