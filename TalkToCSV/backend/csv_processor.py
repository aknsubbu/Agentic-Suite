"""Module for processing CSV files and generating basic analytics."""

import os
import pandas as pd
import numpy as np
import json
import base64
import uuid
import shutil
from typing import Dict, List, Any, Optional, Tuple
import logging
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVProcessor:
    """Class for handling CSV file operations and analysis."""
    
    def __init__(self):
        """Initialize the CSV processor."""
        # Define upload directory
        self.UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        
        self.csv_cache = {}  # Store DataFrames in memory for quick access
    
    def process_chunk(self, file_id: str, chunk_number: int, data: str, is_last: bool) -> Dict[str, Any]:
        """Process a chunk of a CSV file.
        
        Args:
            file_id: Unique identifier for the file
            chunk_number: Sequence number of this chunk
            data: Base64-encoded data for this chunk
            is_last: Whether this is the last chunk
            
        Returns:
            Status information and file metadata if reassembled
        """
        # Create a temporary directory for chunks if it doesn't exist
        temp_dir = os.path.join(self.UPLOAD_DIR, file_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the chunk
        chunk_path = os.path.join(temp_dir, f"chunk_{chunk_number}")
        with open(chunk_path, "wb") as f:
            f.write(base64.b64decode(data))
        
        # If this is the last chunk, reassemble the file
        if is_last:
            try:
                file_path = os.path.join(self.UPLOAD_DIR, f"{file_id}.csv")
                with open(file_path, "wb") as outfile:
                    for i in range(chunk_number + 1):
                        chunk_path = os.path.join(temp_dir, f"chunk_{i}")
                        if os.path.exists(chunk_path):
                            with open(chunk_path, "rb") as infile:
                                outfile.write(infile.read())
                
                # Process the reassembled CSV file
                return self.process_csv(file_path, file_id)
            except Exception as e:
                logger.error(f"Error reassembling CSV file: {str(e)}")
                return {"status": "error", "message": f"Error reassembling CSV file: {str(e)}"}
            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir)
        
        return {"status": "success", "message": f"Chunk {chunk_number} received"}
    
    def process_csv(self, file_path: str, file_id: str) -> Dict[str, Any]:
        """Process a CSV file and generate basic metadata and statistics.
        
        Args:
            file_path: Path to the CSV file
            file_id: Unique identifier for the file
            
        Returns:
            Metadata and basic statistics for the CSV file
        """
        try:
            # Try to read with different options to handle various CSV formats
            try:
                df = pd.read_csv(file_path)
            except Exception:
                # Try with different encoding
                try:
                    df = pd.read_csv(file_path, encoding='latin1')
                except Exception:
                    # Try with different delimiter
                    try:
                        df = pd.read_csv(file_path, delimiter=';')
                    except Exception:
                        # Try with both different encoding and delimiter
                        df = pd.read_csv(file_path, encoding='latin1', delimiter=';')
            
            # Cache the DataFrame for future use
            self.csv_cache[file_id] = df
            
            # Generate basic metadata
            metadata = self._generate_metadata(df, file_id)
            
            # Generate basic analysis
            analysis = self.generate_analysis(file_id)
            
            return {
                "status": "success",
                "file_id": file_id,
                "metadata": metadata,
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            return {"status": "error", "message": f"Error processing CSV file: {str(e)}"}
    
    def _generate_metadata(self, df: pd.DataFrame, file_id: str) -> Dict[str, Any]:
        """Generate metadata for a DataFrame.
        
        Args:
            df: Pandas DataFrame
            file_id: File identifier
            
        Returns:
            Metadata dictionary
        """
        return {
            "file_id": file_id,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "sample_rows": df.head(5).to_dict(orient='records')
        }
    
    def generate_analysis(self, file_id: str) -> Dict[str, Any]:
        """Generate comprehensive analysis for a CSV file.
        
        Args:
            file_id: Identifier for the cached DataFrame
            
        Returns:
            Dictionary with various analyses
        """
        if file_id not in self.csv_cache:
            return {"status": "error", "message": "File not found in cache"}
        
        df = self.csv_cache[file_id]
        
        try:
            analysis = {
                "summary_stats": self._generate_summary_stats(df),
                "data_quality": self._check_data_quality(df),
                "correlations": self._calculate_correlations(df),
                "visualizations": self._recommend_visualizations(df)
            }
            return analysis
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return {"status": "error", "message": f"Error generating analysis: {str(e)}"}
    
    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for all columns.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "numeric_columns": df.select_dtypes(include=np.number).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=np.datetime64).columns.tolist(),
            "column_stats": {}
        }
        
        # Generate per-column statistics
        for col in df.columns:
            col_stats = {
                "type": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_percentage": float((df[col].isna().sum() / len(df)) * 100)
            }
            
            # Numeric column stats
            if pd.api.types.is_numeric_dtype(df[col]):
                non_null = df[col].dropna()
                if not non_null.empty:
                    col_stats.update({
                        "min": float(non_null.min()) if not pd.isna(non_null.min()) else None,
                        "max": float(non_null.max()) if not pd.isna(non_null.max()) else None,
                        "mean": float(non_null.mean()) if not pd.isna(non_null.mean()) else None,
                        "median": float(non_null.median()) if not pd.isna(non_null.median()) else None,
                        "std": float(non_null.std()) if not pd.isna(non_null.std()) else None
                    })
            
            # Categorical/string column stats
            elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                non_null = df[col].dropna()
                if not non_null.empty:
                    value_counts = non_null.value_counts()
                    col_stats.update({
                        "unique_count": int(non_null.nunique()),
                        "top_values": {str(k): int(v) for k, v in value_counts.head(5).items()}
                    })
            
            # Date column stats
            elif pd.api.types.is_datetime64_dtype(df[col]):
                non_null = df[col].dropna()
                if not non_null.empty:
                    col_stats.update({
                        "min": str(non_null.min()),
                        "max": str(non_null.max()),
                        "range_days": (non_null.max() - non_null.min()).days
                    })
            
            summary["column_stats"][col] = col_stats
        
        return summary
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data quality issues in the DataFrame.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Dictionary with data quality metrics
        """
        quality = {
            "missing_values": {
                "total_missing": int(df.isna().sum().sum()),
                "missing_percentage": float((df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100),
                "columns_with_missing": {
                    col: int(df[col].isna().sum()) 
                    for col in df.columns if df[col].isna().sum() > 0
                }
            },
            "duplicates": {
                "duplicate_rows": int(df.duplicated().sum()),
                "duplicate_percentage": float((df.duplicated().sum() / len(df)) * 100)
            }
        }
        
        # Check for potential outliers in numeric columns
        outliers = {}
        for col in df.select_dtypes(include=np.number).columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                Q1 = non_null.quantile(0.25)
                Q3 = non_null.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_count = ((non_null < lower_bound) | (non_null > upper_bound)).sum()
                if outlier_count > 0:
                    outliers[col] = {
                        "outlier_count": int(outlier_count),
                        "outlier_percentage": float((outlier_count / len(non_null)) * 100),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound)
                    }
        
        quality["outliers"] = outliers
        
        return quality
    
    def _calculate_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlations between numeric columns.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Dictionary with correlation data
        """
        numeric_df = df.select_dtypes(include=np.number)
        
        if numeric_df.shape[1] < 2:
            return {"status": "not_applicable", "message": "Not enough numeric columns for correlation"}
        
        try:
            # Calculate correlations
            corr_matrix = numeric_df.corr().round(3)
            
            # Find top correlations (both positive and negative)
            correlations = []
            for col1 in corr_matrix.columns:
                for col2 in corr_matrix.columns:
                    if col1 != col2 and abs(corr_matrix.loc[col1, col2]) > 0.5:
                        correlations.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": float(corr_matrix.loc[col1, col2])
                        })
            
            # Sort by absolute correlation value
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            # Remove duplicates (since correlation matrix is symmetric)
            unique_correlations = []
            seen_pairs = set()
            for corr in correlations:
                pair = tuple(sorted([corr["column1"], corr["column2"]]))
                if pair not in seen_pairs:
                    unique_correlations.append(corr)
                    seen_pairs.add(pair)
            
            return {
                "correlation_matrix": corr_matrix.to_dict(),
                "top_correlations": unique_correlations[:10]  # Limit to top 10
            }
        except Exception as e:
            logger.error(f"Error calculating correlations: {str(e)}")
            return {"status": "error", "message": f"Error calculating correlations: {str(e)}"}
    
    def _recommend_visualizations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Recommend appropriate visualizations for the data.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            List of visualization recommendations
        """
        visualizations = []
        
        # Get column types
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = []
        
        # Check for datetime columns (including string columns that could be dates)
        for col in df.columns:
            if pd.api.types.is_datetime64_dtype(df[col]):
                datetime_cols.append(col)
            elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                # Try to convert to datetime
                try:
                    pd.to_datetime(df[col], errors='raise')
                    datetime_cols.append(col)
                except:
                    pass
        
        # Distribution of numeric columns
        for col in numeric_cols[:3]:  # Limit to first 3
            visualizations.append({
                "type": "histogram",
                "title": f"Distribution of {col}",
                "description": f"Histogram showing the distribution of values for {col}",
                "config": {
                    "x": col,
                    "nbins": min(30, max(10, int(df[col].nunique() / 2))) if df[col].nunique() < 100 else 30
                }
            })
        
        # Bar charts for categorical columns
        for col in categorical_cols[:3]:  # Limit to first 3
            if df[col].nunique() <= 15:  # Only if not too many unique values
                visualizations.append({
                    "type": "bar",
                    "title": f"Count of {col}",
                    "description": f"Bar chart showing counts for each value of {col}",
                    "config": {
                        "x": col,
                        "y": "count"
                    }
                })
        
        # Time series for datetime + numeric columns
        if datetime_cols and numeric_cols:
            for date_col in datetime_cols[:1]:  # First date column
                for num_col in numeric_cols[:2]:  # First 2 numeric columns
                    visualizations.append({
                        "type": "line",
                        "title": f"{num_col} over {date_col}",
                        "description": f"Line chart showing {num_col} values over time",
                        "config": {
                            "x": date_col,
                            "y": num_col
                        }
                    })
        
        # Scatter plots for numeric columns
        if len(numeric_cols) >= 2:
            for i, col1 in enumerate(numeric_cols[:3]):  # Limit to avoid too many combinations
                for col2 in numeric_cols[i+1:min(i+3, len(numeric_cols))]:
                    visualizations.append({
                        "type": "scatter",
                        "title": f"{col1} vs {col2}",
                        "description": f"Scatter plot showing relationship between {col1} and {col2}",
                        "config": {
                            "x": col1,
                            "y": col2
                        }
                    })
        
        # Heatmap for correlation matrix if enough numeric columns
        if len(numeric_cols) >= 4:
            visualizations.append({
                "type": "heatmap",
                "title": "Correlation Matrix",
                "description": "Heatmap showing correlations between numeric columns",
                "config": {
                    "columns": numeric_cols
                }
            })
        
        # Box plots for numeric columns, grouped by categorical if available
        for num_col in numeric_cols[:3]:
            if categorical_cols and df[categorical_cols[0]].nunique() <= 10:
                visualizations.append({
                    "type": "box",
                    "title": f"{num_col} by {categorical_cols[0]}",
                    "description": f"Box plot showing distribution of {num_col} across {categorical_cols[0]} categories",
                    "config": {
                        "x": categorical_cols[0],
                        "y": num_col
                    }
                })
            else:
                visualizations.append({
                    "type": "box",
                    "title": f"Distribution of {num_col}",
                    "description": f"Box plot showing distribution of {num_col}",
                    "config": {
                        "y": num_col
                    }
                })
        
        return visualizations
    
    def get_dataframe(self, file_id: str) -> Optional[pd.DataFrame]:
        """Retrieve a DataFrame from the cache.
        
        Args:
            file_id: File identifier
            
        Returns:
            Pandas DataFrame or None if not found
        """
        return self.csv_cache.get(file_id)
    
    def get_dataframe_info(self, file_id: str) -> Dict[str, Any]:
        """Get information about a DataFrame for use in prompts.
        
        Args:
            file_id: File identifier
            
        Returns:
            Dictionary with DataFrame information
        """
        df = self.get_dataframe(file_id)
        if df is None:
            return {"status": "error", "message": "File not found in cache"}
        
        return {
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "shape": df.shape,
            "sample": df.head(5).to_dict(orient='records'),
            "numeric_columns": df.select_dtypes(include=np.number).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=np.datetime64).columns.tolist(),
        }

# Create a singleton instance
csv_processor = CSVProcessor()