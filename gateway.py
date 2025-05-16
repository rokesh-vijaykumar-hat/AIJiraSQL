"""
API Gateway module for routing requests between services
"""
import os
import json
import requests
import logging
import asyncio
from flask import Blueprint, request, jsonify

from database import DatabaseConnection
from jira_service import JiraService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a blueprint for the gateway routes
gateway_bp = Blueprint('gateway', __name__)

# AI Agent service URL - configurable from environment for Docker Compose
AI_AGENT_URL = os.environ.get('AI_AGENT_URL', 'http://localhost:8080')

# Initialize services
db_connection = DatabaseConnection()
jira_service = JiraService()

@gateway_bp.route('/api/health', methods=['GET'])
def check_health():
    """Check health of all services"""
    health_status = {
        'gateway': 'healthy',
        'ai_agent': 'unknown',
        'database': 'unknown',
        'jira': 'unknown'
    }
    
    # Check AI Agent health
    try:
        ai_response = requests.get(f"{AI_AGENT_URL}/health", timeout=5)
        if ai_response.status_code == 200:
            health_status['ai_agent'] = 'healthy'
        else:
            health_status['ai_agent'] = 'unhealthy'
    except Exception as e:
        health_status['ai_agent'] = f'error: {str(e)}'
    
    # Check database health
    if db_connection.is_configured:
        try:
            if db_connection.check_connection():
                health_status['database'] = 'connected'
            else:
                health_status['database'] = 'error: could not connect'
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
    else:
        health_status['database'] = 'not configured'
    
    # Check Jira health
    if jira_service.is_configured:
        health_status['jira'] = 'configured'
    else:
        health_status['jira'] = 'not configured'
    
    return jsonify({
        'status': 'ok' if all(v in ['healthy', 'connected', 'configured'] for v in health_status.values()) else 'degraded',
        'services': health_status
    })

@gateway_bp.route('/api/jira/issues/<issue_key>', methods=['GET'])
def get_jira_issue(issue_key):
    """Get a Jira issue by key"""
    if not jira_service.is_configured:
        return jsonify({
            'success': False,
            'message': 'Jira integration is not configured'
        }), 503
    
    try:
        # Use asyncio to run coroutine
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        issue = loop.run_until_complete(jira_service.get_issue(issue_key))
        loop.close()
        
        return jsonify({
            'success': True,
            'data': issue,
            'message': 'Issue retrieved successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving Jira issue: {str(e)}'
        }), 500

@gateway_bp.route('/api/jira/context/<issue_key>', methods=['GET'])
def get_jira_context(issue_key):
    """Extract context from a Jira issue"""
    if not jira_service.is_configured:
        return jsonify({
            'success': False,
            'message': 'Jira integration is not configured'
        }), 503
    
    try:
        # Use asyncio to run coroutine
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        context = loop.run_until_complete(jira_service.extract_context(issue_key))
        loop.close()
        
        return jsonify({
            'success': True,
            'data': {
                'issue_key': issue_key,
                'context': context
            },
            'message': 'Context extracted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error extracting context: {str(e)}'
        }), 500

@gateway_bp.route('/api/sql/generate', methods=['POST'])
def generate_sql():
    """Route natural language to SQL requests to the AI Agent"""
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({
            'success': False,
            'message': 'Query is required'
        }), 400
    
    # Get schema info from database
    schema_info = db_connection.get_schema_info()
    
    # Prepare request for AI Agent
    ai_request = {
        'query': data['query'],
        'schema_info': schema_info
    }
    
    # Add Jira context if issue key is provided
    if 'jira_issue_key' in data and data['jira_issue_key']:
        try:
            # Use asyncio to run coroutine
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            jira_context = loop.run_until_complete(jira_service.extract_context(data['jira_issue_key']))
            loop.close()
            
            ai_request['jira_context'] = jira_context
        except Exception as e:
            logger.warning(f"Could not extract Jira context: {str(e)}")
    
    # Add additional context if provided
    if 'additional_context' in data and data['additional_context']:
        ai_request['additional_context'] = data['additional_context']
    
    try:
        # Forward request to AI Agent
        response = requests.post(
            f"{AI_AGENT_URL}/generate-sql",
            json=ai_request,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'AI Agent returned error: {response.text}'
            }), response.status_code
        
        # Return the AI Agent response
        result = response.json()
        return jsonify({
            'success': True,
            'data': {
                'sql': result['sql_query'],
                'explanation': result['explanation']
            },
            'message': 'Query generated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error communicating with AI Agent: {str(e)}'
        }), 500

@gateway_bp.route('/api/sql/execute', methods=['POST'])
def execute_sql():
    """
    Execute an SQL query generated from natural language.
    This endpoint will:
    1. Convert the natural language to SQL via the AI Agent
    2. Execute the SQL query against the database
    3. Use the AI Agent to explain the results
    """
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({
            'success': False,
            'message': 'Query is required'
        }), 400
    
    # Step 1: Generate SQL via AI Agent
    schema_info = db_connection.get_schema_info()
    
    # Prepare request for AI Agent
    ai_request = {
        'query': data['query'],
        'schema_info': schema_info
    }
    
    # Add Jira context if issue key is provided
    jira_context = None
    if 'jira_issue_key' in data and data['jira_issue_key']:
        try:
            # Use asyncio to run coroutine
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            jira_context = loop.run_until_complete(jira_service.extract_context(data['jira_issue_key']))
            loop.close()
            
            ai_request['jira_context'] = jira_context
        except Exception as e:
            logger.warning(f"Could not extract Jira context: {str(e)}")
    
    # Add additional context if provided
    if 'additional_context' in data and data['additional_context']:
        ai_request['additional_context'] = data['additional_context']
    
    try:
        # Step 1: Get SQL from AI Agent
        sql_response = requests.post(
            f"{AI_AGENT_URL}/generate-sql",
            json=ai_request,
            timeout=30
        )
        
        if sql_response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'Failed to generate SQL: {sql_response.text}'
            }), sql_response.status_code
        
        sql_result = sql_response.json()
        sql_query = sql_result['sql_query']
        
        # Step 2: Execute SQL query against database
        query_result = db_connection.execute_query(sql_query)
        
        # Step 3: Get AI to explain the results
        explain_response = requests.post(
            f"{AI_AGENT_URL}/explain-results",
            json={
                'query': data['query'],
                'sql': sql_query,
                'results': query_result['results'],
                'jira_context': jira_context
            },
            timeout=30
        )
        
        explanation = "Could not generate explanation."
        if explain_response.status_code == 200:
            explanation = explain_response.json()['explanation']
        
        # Return complete response
        return jsonify({
            'success': True,
            'data': {
                'sql': sql_query,
                'results': query_result['results'],
                'row_count': query_result['row_count'],
                'execution_time_ms': query_result['execution_time_ms'],
                'explanation': explanation
            },
            'message': 'Query executed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error executing query: {str(e)}'
        }), 500

@gateway_bp.route('/api/db/schema', methods=['GET'])
def get_schema():
    """Get database schema information"""
    try:
        schema = db_connection.get_schema_info()
        return jsonify({
            'success': True,
            'data': schema,
            'message': 'Schema retrieved successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving schema: {str(e)}'
        }), 500