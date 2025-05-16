from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import openai
from openai import OpenAI
import json
import time

# Check for OpenAI API key
if not os.environ.get("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not set. AI functionality will not work.")

# Initialize the OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
    Generate SQL from natural language using OpenAI's GPT-4o model.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
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
        result = json.loads(response.choices[0].message.content)
        
        print(f"Query generation time: {end_time - start_time:.2f} seconds")
        return SQLResponse(
            sql_query=result["sql_query"],
            explanation=result["explanation"]
        )
    
    except Exception as e:
        print(f"Error generating SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(e)}")

@app.post("/explain-results")
async def explain_results(
    query: str,
    sql: str,
    results: List[Dict[str, Any]],
    jira_context: Optional[str] = None
):
    """
    Explain SQL query results in natural language using OpenAI's GPT-4o model.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
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
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}]
        )
        
        explanation = response.choices[0].message.content
        
        return {"explanation": explanation}
    
    except Exception as e:
        print(f"Error explaining results: {e}")
        raise HTTPException(status_code=500, detail=f"Error explaining results: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)