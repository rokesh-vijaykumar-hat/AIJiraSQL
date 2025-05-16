"""
Mock AI service for testing without external API keys.
This module provides mock AI responses for SQL generation and explanation.
"""
import logging
import json
import random
import time
from typing import Dict, Any, List, Optional


class MockAIService:
    """
    Mock service that simulates AI responses for testing purposes.
    """
    
    def __init__(self):
        logging.info("Initializing Mock AI Service for local testing")
    
    def generate_sql(self, query: str, schema_info: Dict[str, Any], 
                    jira_context: Optional[str] = None, 
                    additional_context: Optional[str] = None) -> Dict[str, str]:
        """
        Generate mock SQL based on the natural language query and schema.
        """
        logging.info(f"Generating mock SQL for query: {query}")
        
        # Add a slight delay to simulate processing time
        time.sleep(0.5)
        
        # Generate different SQL based on keywords in the query
        sql_query = ""
        explanation = ""
        
        # Extract table names from schema for use in the queries
        tables = [table["name"] for table in schema_info.get("tables", [])]
        
        if not tables:
            tables = ["customers", "orders", "products", "order_items"]
        
        if "customer" in query.lower():
            sql_query = f"SELECT * FROM {tables[0]} WHERE 1=1"
            
            if "high value" in query.lower() or "top" in query.lower():
                sql_query = f"""
                SELECT c.*, SUM(o.amount) as total_spent 
                FROM {tables[0]} c
                JOIN {tables[1]} o ON c.id = o.customer_id
                GROUP BY c.id
                ORDER BY total_spent DESC
                LIMIT 10
                """
                explanation = "This query finds the top spending customers by calculating their total order amounts."
            
            elif "recent" in query.lower():
                sql_query = f"""
                SELECT c.* 
                FROM {tables[0]} c
                JOIN {tables[1]} o ON c.id = o.customer_id
                WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
                """
                explanation = "This query returns customers who have placed orders in the last 30 days."
            
            else:
                explanation = "This query returns all customers in the database."
        
        elif "order" in query.lower() or "purchase" in query.lower():
            sql_query = f"SELECT * FROM {tables[1]} WHERE 1=1"
            
            if "last month" in query.lower() or "recent" in query.lower():
                sql_query = f"""
                SELECT * 
                FROM {tables[1]}
                WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
                """
                explanation = "This query finds orders placed in the last 30 days."
            
            elif "high value" in query.lower() or "expensive" in query.lower() or "over" in query.lower():
                sql_query = f"""
                SELECT *
                FROM {tables[1]}
                WHERE amount > 1000
                ORDER BY amount DESC
                """
                explanation = "This query returns high-value orders (over $1000) sorted by amount."
            
            else:
                explanation = "This query returns all orders in the database."
        
        elif "product" in query.lower():
            sql_query = f"SELECT * FROM {tables[2]} WHERE 1=1"
            
            if "inventory" in query.lower() or "stock" in query.lower():
                sql_query = f"""
                SELECT *
                FROM {tables[2]}
                WHERE inventory < 20
                ORDER BY inventory ASC
                """
                explanation = "This query finds products with low inventory (less than 20 units)."
            
            elif "popular" in query.lower() or "best selling" in query.lower():
                sql_query = f"""
                SELECT p.*, COUNT(oi.product_id) as units_sold
                FROM {tables[2]} p
                JOIN {tables[3]} oi ON p.id = oi.product_id
                GROUP BY p.id
                ORDER BY units_sold DESC
                LIMIT 10
                """
                explanation = "This query returns the top 10 best-selling products based on order item count."
            
            else:
                explanation = "This query returns all products in the database."
        
        else:
            # Default query if no specific keywords are found
            table = random.choice(tables)
            sql_query = f"SELECT * FROM {table} LIMIT 10"
            explanation = f"This query returns a sample of 10 records from the {table} table."
        
        return {
            "sql_query": sql_query.strip(),
            "explanation": explanation
        }
    
    def explain_results(self, query: str, sql: str, results: List[Dict[str, Any]], 
                        jira_context: Optional[str] = None) -> str:
        """
        Generate a mock explanation of SQL query results.
        """
        logging.info(f"Generating mock explanation for query results")
        
        # Add a slight delay to simulate processing time
        time.sleep(0.3)
        
        # Generate an explanation based on the results
        row_count = len(results)
        
        if row_count == 0:
            return "The query returned no results, which means no records matched the specified criteria."
        
        explanation = f"The query returned {row_count} result"
        explanation += "s" if row_count != 1 else ""
        
        # Add some details based on the results
        if row_count > 0 and row_count <= 10:
            # Extract some sample data for the explanation
            sample = results[0]
            keys = list(sample.keys())
            
            # Try to make a meaningful explanation based on available columns
            if "name" in sample:
                names = [str(r.get("name", "")) for r in results if "name" in r and r.get("name") is not None]
                if names:
                    explanation += f". The data includes: {', '.join(names[:3])}"
                    if len(names) > 3:
                        explanation += f", and {len(names) - 3} others"
            
            if "amount" in sample or "price" in sample or "total_spent" in sample:
                # Find the column that might contain monetary values
                monetary_col = None
                for col in ["amount", "price", "total_spent"]:
                    if col in sample:
                        monetary_col = col
                        break
                
                if monetary_col:
                    # Extract values, ensuring they are numeric
                    values = []
                    for r in results:
                        if monetary_col in r and r.get(monetary_col) is not None:
                            try:
                                val = float(r.get(monetary_col))
                                values.append(val)
                            except (TypeError, ValueError):
                                pass
                    
                    if values:
                        total = sum(values)
                        avg = total / len(values)
                        max_val = max(values)
                        explanation += f". The total {monetary_col} is ${total:.2f}, with an average of ${avg:.2f}. The highest {monetary_col} is ${max_val:.2f}."
        
        # Add some general insights
        explanation += " This information can help with business decisions related to "
        
        if "customer" in sql.lower():
            explanation += "customer relationship management and targeting high-value customers."
        elif "order" in sql.lower() or "purchase" in sql.lower():
            explanation += "sales analysis, inventory management, and forecasting."
        elif "product" in sql.lower():
            explanation += "product strategy, pricing, and inventory management."
        else:
            explanation += "business intelligence and data-driven decision making."
        
        return explanation