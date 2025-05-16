import re
from typing import Dict, Any, List, Optional
import json

def sanitize_sql(sql: str) -> str:
    """
    Sanitize a SQL query by removing potentially harmful parts.
    
    Args:
        sql: The SQL query to sanitize
        
    Returns:
        Sanitized SQL query
    """
    # Remove comments
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    # Remove multiple semicolons (which could be used to chain queries)
    sql = re.sub(r';;+', ';', sql)
    
    # Remove leading and trailing whitespace
    sql = sql.strip()
    
    return sql

def format_error_response(error: Exception) -> Dict[str, Any]:
    """
    Format an error response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Formatted error response
    """
    return {
        "success": False,
        "data": None,
        "message": str(error)
    }

def truncate_large_results(results: List[Dict[str, Any]], max_rows: int = 1000) -> List[Dict[str, Any]]:
    """
    Truncate large result sets to prevent overwhelming responses.
    
    Args:
        results: The query results
        max_rows: Maximum number of rows to return
        
    Returns:
        Truncated results
    """
    if len(results) > max_rows:
        return results[:max_rows]
    return results

def format_sql_for_display(sql: str) -> str:
    """
    Format SQL query for display in API responses.
    
    Args:
        sql: The SQL query to format
        
    Returns:
        Formatted SQL query
    """
    # Replace multiple spaces with a single space
    sql = re.sub(r' +', ' ', sql)
    
    # Capitalize SQL keywords
    keywords = [
        'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
        'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
        'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN',
        'UNION', 'ALL', 'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'IS NULL', 'IS NOT NULL', 'LIMIT', 'OFFSET'
    ]
    
    for keyword in keywords:
        pattern = r'\b' + keyword.replace(' ', r'\s+') + r'\b'
        sql = re.sub(pattern, keyword, sql, flags=re.IGNORECASE)
    
    return sql

def parse_json_safely(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse a JSON string safely, returning None if parsing fails.
    
    Args:
        json_str: The JSON string to parse
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None
