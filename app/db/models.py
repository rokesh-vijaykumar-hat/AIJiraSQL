from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

# This file provides sample models that might be present in the database
# The actual models would depend on the specific database schema

class QueryHistory(Base):
    """
    Model to store history of executed queries.
    """
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    natural_language_query = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    row_count = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    jira_issue_key = Column(String(20), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<QueryHistory(id={self.id}, sql_query='{self.sql_query[:30]}...', success={self.success})>"

class DatabaseSchema(Base):
    """
    Model to store database schema information.
    """
    __tablename__ = "database_schema"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False)
    column_name = Column(String(100), nullable=False)
    data_type = Column(String(50), nullable=False)
    is_nullable = Column(Boolean, default=True, nullable=False)
    is_primary_key = Column(Boolean, default=False, nullable=False)
    is_foreign_key = Column(Boolean, default=False, nullable=False)
    references_table = Column(String(100), nullable=True)
    references_column = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DatabaseSchema(table={self.table_name}, column={self.column_name}, type={self.data_type})>"
