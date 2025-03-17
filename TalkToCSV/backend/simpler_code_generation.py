"""Module for handling simple descriptive queries with predefined code."""

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCodeGenerator:
    """Provides predefined code snippets for common query types."""
    
    def __init__(self):
        """Initialize the simple code generator."""
        # Dictionary of query patterns and corresponding code
        self.query_patterns = {
            "what is the data about": self._data_overview_code,
            "what is in the data": self._data_overview_code,
            "what is the file about": self._data_overview_code,
            "what does the data contain": self._data_overview_code,
            "show me the data": self._show_data_code,
            "display the data": self._show_data_code,
            "basic statistics": self._basic_stats_code,
            "summary statistics": self._basic_stats_code,
            "summary of data": self._basic_stats_code,
            "explain the dataset": self._explain_dataset_code,
            "explain the data": self._explain_dataset_code,
            "tell me about the data": self._explain_dataset_code,
            "describe the dataset": self._explain_dataset_code,
        }
    
    def get_simple_code(self, query: str) -> Optional[Dict[str, Any]]:
        """Check if query matches a simple pattern and return predefined code.
        
        Args:
            query: User's query string
            
        Returns:
            Dictionary with code and visualization type, or None if no match
        """
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Check for direct matches
        for pattern, code_generator in self.query_patterns.items():
            if pattern in normalized_query:
                return code_generator()
        
        # No match found
        return None
    
    def _data_overview_code(self) -> Dict[str, Any]:
        """Generate code for providing a data overview."""
        code = """# Display basic information about the data
info = {
    "rows": len(df),
    "columns": list(df.columns),
    "column_types": {col: str(df[col].dtype) for col in df.columns},
    "sample_data": df.head(5).to_dict(orient='records')
}

# Count unique values in each column
unique_values = {}
for col in df.columns:
    unique_values[col] = df[col].nunique()
    
info["unique_values"] = unique_values

# Add a summary of numeric columns if any exist
numeric_cols = df.select_dtypes(include=['number']).columns
if len(numeric_cols) > 0:
    info["numeric_summary"] = df[numeric_cols].describe().to_dict()

result = info
"""
        return {
            "code": code,
            "visualization_type": "none",
            "explanation": "This code provides an overview of the data, including its structure, column types, and basic statistics."
        }
    
    def _show_data_code(self) -> Dict[str, Any]:
        """Generate code for displaying data."""
        code = """# Display the first 10 rows of the dataset
result = df.head(10)
"""
        return {
            "code": code,
            "visualization_type": "table",
            "explanation": "This code displays the first 10 rows of your data."
        }
    
    def _basic_stats_code(self) -> Dict[str, Any]:
        """Generate code for basic statistics."""
        code = """# Generate basic statistics for each column
stats = {}

# For numeric columns, use describe()
numeric_cols = df.select_dtypes(include=['number']).columns
if len(numeric_cols) > 0:
    stats["numeric"] = df[numeric_cols].describe().to_dict()

# For categorical columns, get value counts
cat_cols = df.select_dtypes(include=['object', 'category']).columns
if len(cat_cols) > 0:
    stats["categorical"] = {}
    for col in cat_cols:
        stats["categorical"][col] = df[col].value_counts().head(5).to_dict()

# Count missing values
stats["missing_values"] = df.isnull().sum().to_dict()

# Get row and column counts
stats["shape"] = {"rows": df.shape[0], "columns": df.shape[1]}

result = stats
"""
        return {
            "code": code,
            "visualization_type": "none",
            "explanation": "This code provides basic statistics about the data, including descriptive statistics for numeric columns and value counts for categorical columns."
        }
    
    def _explain_dataset_code(self) -> Dict[str, Any]:
        """Generate code for explaining the dataset."""
        code = """# Comprehensive explanation of the dataset
explanation = {}

# Basic information
explanation["basic_info"] = {
    "row_count": len(df),
    "column_count": len(df.columns),
    "columns": list(df.columns),
    "dtypes": {col: str(df[col].dtype) for col in df.columns}
}

# Sample data
explanation["sample"] = df.head(5).to_dict(orient='records')

# Numeric statistics (if any numeric columns exist)
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
if numeric_cols:
    explanation["numeric_stats"] = {}
    for col in numeric_cols:
        explanation["numeric_stats"][col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "std": float(df[col].std())
        }

# Categorical column information
cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
if cat_cols:
    explanation["categorical_stats"] = {}
    for col in cat_cols:
        # Get top 5 values and their counts
        value_counts = df[col].value_counts().head(5)
        explanation["categorical_stats"][col] = {
            "unique_count": df[col].nunique(),
            "top_values": {str(k): int(v) for k, v in value_counts.items()}
        }

# Missing values
explanation["missing_values"] = {
    col: int(df[col].isna().sum()) 
    for col in df.columns 
    if df[col].isna().sum() > 0
}

# Set result to return
result = explanation
"""
        return {
            "code": code,
            "visualization_type": "none",
            "explanation": "This code provides a comprehensive explanation of the dataset, including basic information, sample data, statistics for numeric columns, and information about categorical columns."
        }

# Create a singleton instance
simple_code_generator = SimpleCodeGenerator()