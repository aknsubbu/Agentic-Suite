from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd

class DatabaseExplorer(ABC):
    """Abstract base class for database exploration.
    
    Any database connector should implement this interface to work with the agent system.
    """
    
    @abstractmethod
    def explore_database(self) -> Dict:
        """Explore the database structure and return findings
        
        Returns:
            Dict: Information about the database structure including collections/tables,
                 relationships, schemas, etc.
        """
        pass
    
    @abstractmethod
    def execute_query(self, collection_name: str, query_params: Dict) -> pd.DataFrame:
        """Execute a query against the database
        
        Args:
            collection_name: Name of the collection/table to query
            query_params: Dictionary of query parameters (will vary by database type)
            
        Returns:
            pandas.DataFrame: Query results
        """
        pass
    
    @abstractmethod
    def execute_aggregation(self, collection_name: str, aggregation_params: Any) -> pd.DataFrame:
        """Execute an aggregation or analytical query
        
        Args:
            collection_name: Name of the collection/table
            aggregation_params: Aggregation specification (format depends on database)
            
        Returns:
            pandas.DataFrame: Aggregation results
        """
        pass
    
    @abstractmethod
    def generate_notes(self) -> str:
        """Generate human-readable notes about the database structure
        
        Returns:
            str: Markdown-formatted notes describing the database
        """
        pass