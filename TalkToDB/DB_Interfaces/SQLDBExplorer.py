import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, inspect, text

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from dbInterface import DatabaseExplorer

class SQLDatabaseExplorer(DatabaseExplorer):
    """SQL database implementation of the DatabaseExplorer interface"""
    
    def __init__(self, connection_string: str):
        """Initialize with a SQLAlchemy connection string
        
        Args:
            connection_string: SQLAlchemy connection string (e.g., 'sqlite:///mydb.db')
        """
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.inspector = inspect(self.engine)
        self.exploration_notes = {}
        
    def explore_database(self) -> Dict:
        """Perform comprehensive SQL database exploration and return findings"""
        print("Beginning SQL database exploration...")
        
        # Get database name from connection string
        db_name = self.connection_string.split("/")[-1]
        if ":" in db_name:
            db_name = db_name.split(":")[0]
        
        exploration_results = {
            "database_name": db_name,
            "tables": {},
            "relationships": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # List all tables
        tables = self.inspector.get_table_names()
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Explore each table
        for table_name in tables:
            table_info = self._explore_table(table_name)
            exploration_results["tables"][table_name] = table_info
            
        # Identify relationships from foreign keys
        exploration_results["relationships"] = self._identify_relationships()
        
        # Store the exploration results
        self.exploration_notes = exploration_results
        
        return exploration_results
    
    def _explore_table(self, table_name: str) -> Dict:
        """Explore a single table and return its schema and sample data"""
        print(f"Exploring table: {table_name}")
        
        # Get table columns
        columns = self.inspector.get_columns(table_name)
        
        # Get primary key
        primary_key = self.inspector.get_pk_constraint(table_name)
        
        # Get foreign keys
        foreign_keys = self.inspector.get_foreign_keys(table_name)
        
        # Get indexes
        indexes = self.inspector.get_indexes(table_name)
        
        # Get row count
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
        
        # Sample rows (up to 5)
        sample_size = min(count, 5) if count else 0
        sample_rows = []
        
        if sample_size > 0:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {sample_size}"))
                for row in result:
                    # Convert row to dict
                    row_dict = {}
                    for idx, col in enumerate(result.keys()):
                        row_dict[col] = row[idx]
                    sample_rows.append(row_dict)
        
        # Build schema information
        schema = {}
        for column in columns:
            schema[column['name']] = {
                "type": str(column['type']),
                "nullable": column.get('nullable', True),
                "default": str(column.get('default', 'None'))
            }
        
        return {
            "count": count,
            "schema": schema,
            "primary_key": primary_key,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
            "sample_rows": sample_rows
        }
    
    def _identify_relationships(self) -> List[Dict]:
        """Identify relationships between tables based on foreign keys"""
        relationships = []
        
        for table_name in self.inspector.get_table_names():
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            for fk in foreign_keys:
                relationship = {
                    "from_table": table_name,
                    "from_columns": fk['constrained_columns'],
                    "to_table": fk['referred_table'],
                    "to_columns": fk['referred_columns'],
                    "name": fk.get('name', ''),
                    "confidence": "high"  # Foreign keys are explicit relationships
                }
                relationships.append(relationship)
        
        return relationships
    
    def execute_query(self, table_name: str, query_params: Dict) -> pd.DataFrame:
        """Execute a SQL query and return results as a pandas DataFrame
        
        Args:
            table_name: Name of the table (used for simple queries)
            query_params: Dictionary with query parameters:
                          - query: SQL query string (if provided, table_name is ignored)
                          - where: WHERE clause conditions (for simple queries)
                          - limit: Maximum number of results
                          - offset: Number of rows to skip
                          - order_by: ORDER BY clause
                          
        Returns:
            pandas.DataFrame: Query results
        """
        try:
            # Check if a complete SQL query is provided
            if "query" in query_params and query_params["query"]:
                sql_query = query_params["query"]
            else:
                # Build a simple query based on parameters
                sql_query = f"SELECT * FROM {table_name}"
                
                # Add WHERE clause if provided
                if "where" in query_params and query_params["where"]:
                    sql_query += f" WHERE {query_params['where']}"
                
                # Add ORDER BY clause if provided
                if "order_by" in query_params and query_params["order_by"]:
                    sql_query += f" ORDER BY {query_params['order_by']}"
                
                # Add LIMIT clause if provided
                if "limit" in query_params and query_params["limit"]:
                    sql_query += f" LIMIT {query_params['limit']}"
                    
                    # Add OFFSET clause if provided
                    if "offset" in query_params and query_params["offset"]:
                        sql_query += f" OFFSET {query_params['offset']}"
            
            # Execute the query
            df = pd.read_sql(sql_query, self.engine)
            return df
            
        except Exception as e:
            print(f"Error executing SQL query: {str(e)}")
            # Return empty DataFrame with error info
            return pd.DataFrame({"error": [str(e)]})
    
    def execute_aggregation(self, table_name: str, aggregation_params: Dict) -> pd.DataFrame:
        """Execute a SQL aggregation query and return results as a pandas DataFrame
        
        Args:
            table_name: Name of the table (used for building query)
            aggregation_params: Dictionary with aggregation parameters:
                               - group_by: GROUP BY columns
                               - aggregations: Dict of aggregations (col: function)
                               - having: HAVING clause
                               - query: Raw SQL query (if provided, other params ignored)
                               
        Returns:
            pandas.DataFrame: Aggregation results
        """
        try:
            # Check if a complete SQL query is provided
            if "query" in aggregation_params and aggregation_params["query"]:
                sql_query = aggregation_params["query"]
            else:
                # Build aggregation query
                if "group_by" not in aggregation_params or not aggregation_params["group_by"]:
                    raise ValueError("group_by is required for aggregation")
                
                if "aggregations" not in aggregation_params or not aggregation_params["aggregations"]:
                    raise ValueError("aggregations are required")
                
                # Build SELECT clause with aggregations
                group_by_cols = aggregation_params["group_by"]
                agg_cols = []
                
                for col, func in aggregation_params["aggregations"].items():
                    agg_cols.append(f"{func}({col}) AS {func}_{col}")
                
                select_clause = ", ".join(group_by_cols + agg_cols)
                group_by_clause = ", ".join(group_by_cols)
                
                sql_query = f"SELECT {select_clause} FROM {table_name} GROUP BY {group_by_clause}"
                
                # Add HAVING clause if provided
                if "having" in aggregation_params and aggregation_params["having"]:
                    sql_query += f" HAVING {aggregation_params['having']}"
                
                # Add ORDER BY clause if provided
                if "order_by" in aggregation_params and aggregation_params["order_by"]:
                    sql_query += f" ORDER BY {aggregation_params['order_by']}"
                
                # Add LIMIT clause if provided
                if "limit" in aggregation_params and aggregation_params["limit"]:
                    sql_query += f" LIMIT {aggregation_params['limit']}"
            
            # Execute the aggregation query
            df = pd.read_sql(sql_query, self.engine)
            return df
            
        except Exception as e:
            print(f"Error executing SQL aggregation: {str(e)}")
            # Return empty DataFrame with error info
            return pd.DataFrame({"error": [str(e)]})
    
    def generate_notes(self) -> str:
        """Generate readable notes from SQL database exploration results"""
        notes = []
        
        # Handle empty exploration
        if not self.exploration_notes:
            return "Database has not been explored yet. Call explore_database() first."
        
        # Database overview
        notes.append(f"## SQL Database: {self.exploration_notes['database_name']}")
        notes.append(f"Explored on: {self.exploration_notes['timestamp']}")
        notes.append(f"Found {len(self.exploration_notes['tables'])} tables")
        notes.append("")
        
        # Tables summary
        notes.append("## Tables Overview")
        for table_name, table_info in self.exploration_notes['tables'].items():
            notes.append(f"### {table_name}")
            notes.append(f"- Row count: {table_info['count']}")
            notes.append(f"- Columns: {', '.join(table_info['schema'].keys())}")
            
            # Primary key
            if table_info['primary_key'] and table_info['primary_key']['constrained_columns']:
                pk_cols = ", ".join(table_info['primary_key']['constrained_columns'])
                notes.append(f"- Primary Key: {pk_cols}")
            
            notes.append("")
        
        # Relationships
        if self.exploration_notes['relationships']:
            notes.append("## Identified Relationships")
            for relation in self.exploration_notes['relationships']:
                from_cols = ", ".join(relation['from_columns'])
                to_cols = ", ".join(relation['to_columns'])
                notes.append(f"- {relation['from_table']}({from_cols}) → {relation['to_table']}({to_cols})")
            notes.append("")
        
        # Detailed table information
        notes.append("## Table Details")
        for table_name, table_info in self.exploration_notes['tables'].items():
            notes.append(f"### {table_name}")
            notes.append("#### Schema")
            
            for column_name, column_info in table_info['schema'].items():
                notes.append(f"- {column_name}: {column_info['type']}")
                if not column_info['nullable']:
                    notes.append(f"  - NOT NULL")
                if column_info['default'] != 'None':
                    notes.append(f"  - Default: {column_info['default']}")
            
            notes.append("")
            
            # Indexes
            if table_info['indexes']:
                notes.append("#### Indexes")
                for idx in table_info['indexes']:
                    unique = "UNIQUE " if idx['unique'] else ""
                    cols = ", ".join(idx['column_names'])
                    notes.append(f"- {idx['name']}: {unique}({cols})")
                notes.append("")
            
            # Sample data
            if table_info['sample_rows']:
                notes.append("#### Sample Data")
                sample_row = table_info['sample_rows'][0]
                sample_str = json.dumps(sample_row, indent=2, default=str)
                # Truncate if too long
                if len(sample_str) > 500:
                    sample_str = sample_str[:500] + "..."
                notes.append(f"```json\n{sample_str}\n```")
            notes.append("")
        
        return "\n".join(notes)