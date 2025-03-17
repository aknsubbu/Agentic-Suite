from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

import pandas as pd

class DatabaseExplorer(ABC):
    """Abstract interface for database exploration"""
    
    @abstractmethod
    def explore_database(self) -> Dict:
        """Explore the database structure and return findings"""
        pass
    
    @abstractmethod
    def execute_query(self, collection_name: str, query_params: Dict) -> pd.DataFrame:
        """Execute a query and return results as a DataFrame"""
        pass
    
    @abstractmethod
    def execute_aggregation(self, collection_name: str, pipeline: List[Dict]) -> pd.DataFrame:
        """Execute an aggregation pipeline and return results as a DataFrame"""
        pass
    
    @abstractmethod
    def generate_notes(self) -> str:
        """Generate human-readable notes about the database structure"""
        pass