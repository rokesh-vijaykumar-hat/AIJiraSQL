"""
API Gateway module for routing requests between services
"""
import os
import json
import requests
import logging
import asyncio
from flask import Blueprint, request, jsonify

from config import Config
from database import DatabaseConnection
from jira_service import JiraService
from openai_service import OpenAIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a blueprint for the gateway routes
gateway_bp = Blueprint('gateway', __name__)

# Initialize services
db_connection = DatabaseConnection()
jira_service = JiraService()
openai_service = OpenAIService()

@gateway_bp.route('/api/health', methods=['GET'])
def check_health():
    """Check health of all services"""
    health_status = {
        'gateway': 'healthy',
        'database': 'unknown',
        'jira': 'unknown',
        'ai_integration': 'unknown'
    }
    
    # Check the appropriate AI integration based on the configuration
    if Config.is_direct_mode():
        health_status['ai_integration_mode'] = 'direct'
        # Since we've implemented mock functionality, OpenAI is always considered "configured"
        health_status['ai_integration'] = 'configured'
    elif Config.is_agent_mode():
        health_status['ai_integration_mode'] = 'agent'
        
        # Try connecting to the AI Agent service
        try:
            ai_response = requests.get(f"{Config.AI_AGENT_URL}/health", timeout=5)
            if ai_response.status_code == 200:
                health_status['ai_integration'] = 'healthy'
            else:
                health_status['ai_integration'] = 'unhealthy'
        except Exception as e:
            # If AI Agent service is not available, fall back to direct mode with mock implementation
            logger.warning(f"Could not connect to AI Agent service: {str(e)}")
            logger.info("Using direct mode with mock implementation as fallback")
            health_status['ai_integration'] = 'using fallback (direct mode)'
            health_status['ai_integration_mode'] = 'direct (fallback)'
    
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
    """Generate SQL from natural language query using configured AI method"""
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({
            'success': False,
            'message': 'Query is required'
        }), 400
    
    # Get schema info from database
    schema_info = db_connection.get_schema_info()
    
    # Extract Jira context if issue key is provided
    jira_context = None
    if 'jira_issue_key' in data and data['jira_issue_key']:
        try:
            # Use asyncio to run coroutine
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            jira_context = loop.run_until_complete(jira_service.extract_context(data['jira_issue_key']))
            loop.close()
        except Exception as e:
            logger.warning(f"Could not extract Jira context: {str(e)}")
    
    # Get additional context if provided
    additional_context = data.get('additional_context')
    
    try:
        # Choose AI method based on configuration
        if Config.is_direct_mode():
            # Use OpenAI directly with mock fallback
            try:
                # Use asyncio to run coroutine
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    openai_service.generate_sql(
                        data['query'], 
                        schema_info, 
                        jira_context, 
                        additional_context
                    )
                )
                loop.close()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'sql': result['sql_query'],
                        'explanation': result['explanation'],
                        'mode': 'direct'
                    },
                    'message': 'Query generated successfully using OpenAI directly'
                })
            except Exception as e:
                logger.error(f"Error generating SQL using direct OpenAI: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error generating SQL: {str(e)}'
                }), 500
            
        elif Config.is_agent_mode():
            # Use AI Agent service with direct mode fallback
            try:
                # Prepare request for AI Agent
                ai_request = {
                    'query': data['query'],
                    'schema_info': schema_info
                }
                
                # Add context if available
                if jira_context:
                    ai_request['jira_context'] = jira_context
                
                if additional_context:
                    ai_request['additional_context'] = additional_context
                
                # Forward request to AI Agent
                response = requests.post(
                    f"{Config.AI_AGENT_URL}/generate-sql",
                    json=ai_request,
                    timeout=10  # Shorter timeout to fail faster
                )
                
                if response.status_code != 200:
                    raise Exception(f"AI Agent returned error: {response.text}")
                
                # Return the AI Agent response
                result = response.json()
                return jsonify({
                    'success': True,
                    'data': {
                        'sql': result['sql_query'],
                        'explanation': result['explanation'],
                        'mode': 'agent'
                    },
                    'message': 'Query generated successfully using AI Agent'
                })
            except Exception as e:
                # If AI Agent fails, fall back to direct mode
                logger.warning(f"AI Agent service failed: {str(e)}")
                logger.info("Falling back to direct mode")
                
                try:
                    # Use direct mode as fallback
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        openai_service.generate_sql(
                            data['query'], 
                            schema_info, 
                            jira_context, 
                            additional_context
                        )
                    )
                    loop.close()
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'sql': result['sql_query'],
                            'explanation': result['explanation'],
                            'mode': 'direct (fallback)'
                        },
                        'message': 'Query generated successfully using direct mode (fallback)'
                    })
                except Exception as fallback_error:
                    logger.error(f"Fallback to direct mode also failed: {str(fallback_error)}")
                    return jsonify({
                        'success': False,
                        'message': f'Failed to generate SQL: {str(fallback_error)}'
                    }), 500
        
        else:
            return jsonify({
                'success': False,
                'message': f'Invalid AI integration mode: {Config.AI_INTERACTION_MODE}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error generating SQL: {str(e)}'
        }), 500

@gateway_bp.route('/api/sql/execute', methods=['POST'])
def execute_sql():
    """
    Execute an SQL query generated from natural language.
    This endpoint will:
    1. Convert the natural language to SQL using the configured AI method
    2. Execute the SQL query against the database
    3. Use the AI to explain the results
    """
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({
            'success': False,
            'message': 'Query is required'
        }), 400
    
    # Get schema info from database
    schema_info = db_connection.get_schema_info()
    
    # Extract Jira context if issue key is provided
    jira_context = None
    if 'jira_issue_key' in data and data['jira_issue_key']:
        try:
            # Use asyncio to run coroutine
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            jira_context = loop.run_until_complete(jira_service.extract_context(data['jira_issue_key']))
            loop.close()
        except Exception as e:
            logger.warning(f"Could not extract Jira context: {str(e)}")
    
    # Get additional context if provided
    additional_context = data.get('additional_context')
    
    try:
        # Step 1: Generate SQL via configured AI method
        sql_query = None
        ai_mode = None
        
        try:
            if Config.is_direct_mode():
                # Use OpenAI directly with mock fallback
                try:
                    # Use asyncio to run coroutine
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    sql_result = loop.run_until_complete(
                        openai_service.generate_sql(
                            data['query'], 
                            schema_info, 
                            jira_context, 
                            additional_context
                        )
                    )
                    loop.close()
                    
                    sql_query = sql_result['sql_query']
                    ai_mode = 'direct'
                except Exception as e:
                    logger.error(f"Direct OpenAI SQL generation failed: {str(e)}")
                    raise Exception(f"Failed to generate SQL: {str(e)}")
                
            elif Config.is_agent_mode():
                # Use AI Agent service with fallback to direct mode
                try:
                    # Prepare request for AI Agent
                    ai_request = {
                        'query': data['query'],
                        'schema_info': schema_info
                    }
                    
                    # Add context if available
                    if jira_context:
                        ai_request['jira_context'] = jira_context
                    
                    if additional_context:
                        ai_request['additional_context'] = additional_context
                    
                    # Forward request to AI Agent
                    sql_response = requests.post(
                        f"{Config.AI_AGENT_URL}/generate-sql",
                        json=ai_request,
                        timeout=10  # Shorter timeout for faster fallback
                    )
                    
                    if sql_response.status_code != 200:
                        raise Exception(f"AI Agent returned error: {sql_response.text}")
                    
                    sql_result = sql_response.json()
                    sql_query = sql_result['sql_query']
                    ai_mode = 'agent'
                    
                except Exception as e:
                    # If AI Agent fails, fall back to direct mode
                    logger.warning(f"AI Agent SQL generation failed: {str(e)}")
                    logger.info("Falling back to direct mode for SQL generation")
                    
                    # Use direct mode as fallback
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    sql_result = loop.run_until_complete(
                        openai_service.generate_sql(
                            data['query'], 
                            schema_info, 
                            jira_context, 
                            additional_context
                        )
                    )
                    loop.close()
                    
                    sql_query = sql_result['sql_query']
                    ai_mode = 'direct (fallback)'
            else:
                return jsonify({
                    'success': False,
                    'message': f'Invalid AI integration mode: {Config.AI_INTERACTION_MODE}'
                }), 500
            
            # Step 2: Execute SQL query against database
            query_result = db_connection.execute_query(sql_query)
            
            # Step 3: Get AI to explain the results
            explanation = "Could not generate explanation."
            
            if Config.is_direct_mode() or ai_mode == 'direct (fallback)':
                try:
                    # Use OpenAI directly for explanation
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    explanation = loop.run_until_complete(
                        openai_service.explain_results(
                            data['query'],
                            sql_query,
                            query_result['results'],
                            jira_context
                        )
                    )
                    loop.close()
                except Exception as e:
                    logger.warning(f"Could not generate explanation using OpenAI directly: {str(e)}")
                    explanation = f"This query returned {query_result['row_count']} results related to your search."
            
            elif Config.is_agent_mode() and ai_mode == 'agent':
                try:
                    # Use AI Agent for explanation
                    explain_response = requests.post(
                        f"{Config.AI_AGENT_URL}/explain-results",
                        json={
                            'query': data['query'],
                            'sql': sql_query,
                            'results': query_result['results'],
                            'jira_context': jira_context
                        },
                        timeout=10
                    )
                    
                    if explain_response.status_code == 200:
                        explanation = explain_response.json()['explanation']
                    else:
                        # Fallback to direct mode for explanation
                        logger.warning(f"AI Agent explanation failed with status {explain_response.status_code}")
                        logger.info("Falling back to direct mode for results explanation")
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        explanation = loop.run_until_complete(
                            openai_service.explain_results(
                                data['query'],
                                sql_query,
                                query_result['results'],
                                jira_context
                            )
                        )
                        loop.close()
                        
                except Exception as e:
                    logger.warning(f"Could not generate explanation using AI Agent: {str(e)}")
                    logger.info("Falling back to direct mode for results explanation")
                    
                    try:
                        # Fallback to direct mode for explanation
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        explanation = loop.run_until_complete(
                            openai_service.explain_results(
                                data['query'],
                                sql_query,
                                query_result['results'],
                                jira_context
                            )
                        )
                        loop.close()
                    except Exception as fallback_error:
                        logger.error(f"Fallback explanation also failed: {str(fallback_error)}")
                        explanation = f"This query returned {query_result['row_count']} results related to your search."
        
        except Exception as e:
            logger.error(f"Error in SQL execution flow: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error executing query: {str(e)}'
            }), 500
        
        # Return complete response
        return jsonify({
            'success': True,
            'data': {
                'sql': sql_query,
                'results': query_result['results'],
                'row_count': query_result['row_count'],
                'execution_time_ms': query_result['execution_time_ms'],
                'explanation': explanation,
                'mode': ai_mode
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