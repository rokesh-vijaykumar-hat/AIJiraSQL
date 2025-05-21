import os
import time
import logging
from typing import Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Database connection manager for PostgreSQL.
    """
    def __init__(self):
        # Get database configuration from environment variables
        self.db_config = {
            "dbname": os.environ.get("PGDATABASE", ""),
            "user": os.environ.get("PGUSER", ""),
            "password": os.environ.get("PGPASSWORD", ""),
            "host": os.environ.get("PGHOST", ""),
            "port": os.environ.get("PGPORT", "5432")
        }
        
        # Check if database configuration is provided
        if not all([
            self.db_config["dbname"], 
            self.db_config["user"], 
            self.db_config["password"], 
            self.db_config["host"]
        ]):
            raise ValueError("Database connection is not fully configured. Please set PGDATABASE, PGUSER, PGPASSWORD, PGHOST environment variables.")
    
    def get_connection(self):
        """
        Get a database connection.
        
        Returns:
            A database connection object
        
        Raises:
            Exception: If connection fails
        """
        try:
            connection = psycopg2.connect(
                dbname=self.db_config["dbname"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                host=self.db_config["host"],
                port=self.db_config["port"],
                cursor_factory=RealDictCursor
            )
            return connection
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise Exception(f"Could not connect to database: {str(e)}")
        
    def execute_query(self, sql: str) -> Dict[str, Any]:
        sql = sql.strip()
        if not sql:
            logger.error("Attempted to execute an empty SQL query")
            raise ValueError("SQL query is empty and cannot be executed.")
        
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            start_time = time.time()
            cursor.execute(sql)
            end_time = time.time()
            
            if sql.upper().startswith("SELECT"):
                results = cursor.fetchall()
                row_count = len(results)
            else:
                results = []
                row_count = cursor.rowcount if cursor.rowcount >= 0 else 0
                connection.commit()
            
            results_list = [dict(row) for row in results]
            execution_time = (end_time - start_time) * 1000  # ms
            
            cursor.close()
            connection.close()
            
            return {
                "results": results_list,
                "row_count": row_count,
                "execution_time_ms": execution_time
            }
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise


    def get_schema_info(self) -> Dict[str, Any]:
        """
        Retrieve database schema information.
        
        Returns:
            Dictionary containing table and column information
            
        Raises:
            Exception: If retrieval fails
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Get all tables in public schema
            tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """
            cursor.execute(tables_query)
            tables = cursor.fetchall()
            
            schema_info = {"tables": []}
            
            # Get columns and constraints per table
            for table in tables:
                table_name = table["table_name"]
                
                columns_query = """
                    SELECT 
                        c.column_name, 
                        c.data_type,
                        c.is_nullable = 'YES' AS is_nullable,
                        CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END AS is_primary_key,
                        CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END AS is_foreign_key,
                        fk.foreign_table_name AS references_table,
                        fk.foreign_column_name AS references_column
                    FROM information_schema.columns c
                    LEFT JOIN (
                        SELECT kcu.column_name, tc.table_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON kcu.constraint_name = tc.constraint_name AND kcu.table_name = tc.table_name
                        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
                    ) pk ON pk.column_name = c.column_name AND pk.table_name = c.table_name
                    LEFT JOIN (
                        SELECT 
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name,
                            tc.table_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON kcu.constraint_name = tc.constraint_name AND kcu.table_name = tc.table_name
                        JOIN information_schema.constraint_column_usage ccu
                          ON ccu.constraint_name = tc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
                    ) fk ON fk.column_name = c.column_name AND fk.table_name = c.table_name
                    WHERE c.table_name = %s AND c.table_schema = 'public'
                    ORDER BY c.ordinal_position;
                """
                cursor.execute(columns_query, (table_name,))
                columns = cursor.fetchall()
                
                columns_info = []
                for col in columns:
                    col_info = {
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "is_nullable": col["is_nullable"],
                        "is_primary_key": col["is_primary_key"],
                        "is_foreign_key": col["is_foreign_key"]
                    }
                    if col["is_foreign_key"]:
                        col_info["references_table"] = col["references_table"]
                        col_info["references_column"] = col["references_column"]
                    columns_info.append(col_info)
                
                schema_info["tables"].append({
                    "name": table_name,
                    "columns": columns_info
                })
            
            # Get foreign key relationships
            relationships_query = """
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name AND kcu.table_name = tc.table_name
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.column_name;
            """
            cursor.execute(relationships_query)
            relationships = cursor.fetchall()
            
            schema_info["relationships"] = []
            for rel in relationships:
                schema_info["relationships"].append({
                    "from": f"{rel['table_name']}.{rel['column_name']}",
                    "to": f"{rel['foreign_table_name']}.{rel['foreign_column_name']}"
                })
            
            cursor.close()
            connection.close()
            
            return schema_info
        except Exception as e:
            logger.error(f"Error retrieving schema info: {str(e)}")
            raise
    
    def check_connection(self) -> bool:
        """
        Check if the database connection is working.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False
