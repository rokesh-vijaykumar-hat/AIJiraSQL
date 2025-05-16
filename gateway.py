"""
API Gateway module for routing requests between services
"""
import os
import json
import requests
from flask import Blueprint, request, jsonify

# Create a blueprint for the gateway routes
gateway_bp = Blueprint('gateway', __name__)

# AI Agent service URL - configurable from environment for Docker Compose
AI_AGENT_URL = os.environ.get('AI_AGENT_URL', 'http://ai-agent:8080')

@gateway_bp.route('/api/health', methods=['GET'])
def check_health():
    """Check health of all services"""
    health_status = {
        'gateway': 'healthy',
        'ai_agent': 'unknown',
        'database': 'unknown'
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
    
    # Check database health - This would be implemented with a real DB connection
    # For now, we're assuming it's connected if the environment variables are set
    if os.environ.get('DATABASE_URL'):
        health_status['database'] = 'connected'
    
    return jsonify({
        'status': 'ok' if all(v == 'healthy' or v == 'connected' for v in health_status.values()) else 'degraded',
        'services': health_status
    })

@gateway_bp.route('/api/sql/generate', methods=['POST'])
def generate_sql():
    """Route natural language to SQL requests to the AI Agent"""
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({
            'success': False,
            'message': 'Query is required'
        }), 400
    
    # Get schema info from database - this would be a real implementation
    # For demonstration, we'll use a mock schema
    schema_info = get_schema_info()
    
    # Prepare request for AI Agent
    ai_request = {
        'query': data['query'],
        'schema_info': schema_info
    }
    
    # Add optional fields if present
    if 'jira_context' in data:
        ai_request['jira_context'] = data['jira_context']
    
    if 'additional_context' in data:
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
    schema_info = get_schema_info()
    
    # Prepare request for AI Agent
    ai_request = {
        'query': data['query'],
        'schema_info': schema_info
    }
    
    # Add optional fields if present
    if 'jira_context' in data:
        ai_request['jira_context'] = data['jira_context']
    
    if 'additional_context' in data:
        ai_request['additional_context'] = data['additional_context']
    
    try:
        # Get SQL from AI Agent
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
        # This would be a real database query in a production system
        # For demonstration, we'll use mock data
        start_time = 0.0
        query_results = execute_mock_query(sql_query)
        execution_time_ms = 42.5  # Mock execution time
        
        # Step 3: Get AI to explain the results
        explain_response = requests.post(
            f"{AI_AGENT_URL}/explain-results",
            json={
                'query': data['query'],
                'sql': sql_query,
                'results': query_results,
                'jira_context': data.get('jira_context')
            },
            timeout=30
        )
        
        if explain_response.status_code != 200:
            # Return results without explanation if explanation fails
            return jsonify({
                'success': True,
                'data': {
                    'sql': sql_query,
                    'results': query_results,
                    'row_count': len(query_results),
                    'execution_time_ms': execution_time_ms,
                    'explanation': "Could not generate explanation."
                },
                'message': 'Query executed successfully, but explanation failed.'
            })
        
        explanation = explain_response.json()['explanation']
        
        # Return complete response
        return jsonify({
            'success': True,
            'data': {
                'sql': sql_query,
                'results': query_results,
                'row_count': len(query_results),
                'execution_time_ms': execution_time_ms,
                'explanation': explanation
            },
            'message': 'Query executed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error executing query: {str(e)}'
        }), 500

def get_schema_info():
    """
    Get database schema information.
    In a real implementation, this would query the database for its schema.
    For demonstration, we'll return a mock schema.
    """
    return {
        "tables": [
            {
                "name": "customers",
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "name", "type": "varchar(100)"},
                    {"name": "email", "type": "varchar(100)"},
                    {"name": "country", "type": "varchar(50)"},
                    {"name": "created_at", "type": "timestamp"}
                ]
            },
            {
                "name": "orders",
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "customer_id", "type": "integer", "foreign_key": "customers.id"},
                    {"name": "order_date", "type": "date"},
                    {"name": "amount", "type": "decimal(10,2)"},
                    {"name": "status", "type": "varchar(20)"}
                ]
            },
            {
                "name": "products",
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "name", "type": "varchar(100)"},
                    {"name": "category", "type": "varchar(50)"},
                    {"name": "price", "type": "decimal(10,2)"},
                    {"name": "inventory", "type": "integer"}
                ]
            },
            {
                "name": "order_items",
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "order_id", "type": "integer", "foreign_key": "orders.id"},
                    {"name": "product_id", "type": "integer", "foreign_key": "products.id"},
                    {"name": "quantity", "type": "integer"},
                    {"name": "price", "type": "decimal(10,2)"}
                ]
            }
        ],
        "relationships": [
            {"from": "orders.customer_id", "to": "customers.id"},
            {"from": "order_items.order_id", "to": "orders.id"},
            {"from": "order_items.product_id", "to": "products.id"}
        ]
    }

def execute_mock_query(sql_query):
    """
    Execute a mock query and return sample results.
    In a real implementation, this would execute the query against a database.
    """
    # For demonstration, we'll return different mock data based on the query
    if 'customers' in sql_query.lower() and 'orders' not in sql_query.lower():
        return [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "country": "USA", "created_at": "2023-01-15"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "country": "Canada", "created_at": "2023-02-20"},
            {"id": 3, "name": "Robert Brown", "email": "robert@example.com", "country": "UK", "created_at": "2023-03-10"}
        ]
    elif 'orders' in sql_query.lower():
        return [
            {"id": 101, "customer_id": 1, "order_date": "2023-04-05", "amount": 245.50, "status": "Completed"},
            {"id": 102, "customer_id": 1, "order_date": "2023-05-10", "amount": 125.75, "status": "Completed"},
            {"id": 103, "customer_id": 2, "order_date": "2023-04-15", "amount": 89.99, "status": "Completed"},
            {"id": 104, "customer_id": 3, "order_date": "2023-05-20", "amount": 175.25, "status": "Processing"}
        ]
    elif 'products' in sql_query.lower():
        return [
            {"id": 201, "name": "Laptop", "category": "Electronics", "price": 1299.99, "inventory": 45},
            {"id": 202, "name": "Smartphone", "category": "Electronics", "price": 899.99, "inventory": 60},
            {"id": 203, "name": "Headphones", "category": "Accessories", "price": 149.99, "inventory": 100},
            {"id": 204, "name": "Monitor", "category": "Electronics", "price": 349.99, "inventory": 30}
        ]
    else:
        # Default response
        return [{"result": "No data available for this query"}]