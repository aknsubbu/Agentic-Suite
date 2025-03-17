import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from mongoConnect import MongoDBClient
from dbInterface import DatabaseExplorer

class MongoDBExplorer(DatabaseExplorer):
    """MongoDB implementation of the DatabaseExplorer interface"""
    
    def __init__(self, db_name: str, connection_string:str):
        """Initialize with database name"""
        self.db_client = MongoDBClient(db_name,connection_string=connection_string)
        self.exploration_notes = {}
        
    def explore_database(self) -> Dict:
        """Perform comprehensive MongoDB database exploration and return findings"""
        print("Beginning MongoDB database exploration...")
        
        exploration_results = {
            "database_name": self.db_client.db.name,
            "collections": {},
            "relationships": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # List all collections
        collections = self.db_client.list_collections()
        print(f"Found {len(collections)} collections: {', '.join(collections)}")
        
        # Explore each collection
        for collection_name in collections:
            collection_info = self._explore_collection(collection_name)
            exploration_results["collections"][collection_name] = collection_info
            
        # Look for potential relationships between collections
        exploration_results["relationships"] = self._identify_relationships(exploration_results["collections"])
        
        # Store the exploration results
        self.exploration_notes = exploration_results
        
        return exploration_results
    
    def _explore_collection(self, collection_name: str) -> Dict:
        """Explore a single collection and return its schema and sample data"""
        print(f"Exploring collection: {collection_name}")
        
        # Get collection stats
        try:
            stats = self.db_client.get_collection_stats(collection_name)
        except Exception as e:
            stats = {"error": str(e)}
        
        # Get document count
        count = self.db_client.count_documents(collection_name)
        
        # Sample documents (up to 5)
        sample_size = min(count, 5)
        sample_docs = self.db_client.find_many(
            collection_name, 
            limit=sample_size,
            sort=[("_id", 1)]  # Sort by _id for consistent samples
        )
        
        # Infer schema from sample documents
        inferred_schema = self._infer_schema(sample_docs)
        
        # Get indexes
        indexes = list(self.db_client.list_indexes(collection_name))
        
        return {
            "count": count,
            "stats": stats,
            "schema": inferred_schema,
            "indexes": indexes,
            "sample_documents": sample_docs
        }
    
    def _infer_schema(self, documents: List[Dict]) -> Dict:
        """Infer the schema of a collection from sample documents"""
        if not documents:
            return {}
            
        # Combine all document fields
        all_fields = {}
        
        for doc in documents:
            for field, value in doc.items():
                field_type = type(value).__name__
                
                if field in all_fields:
                    # Handle type variations
                    if field_type not in all_fields[field]["types"]:
                        all_fields[field]["types"].append(field_type)
                else:
                    all_fields[field] = {
                        "types": [field_type],
                        "sample": str(value)[:100] + ("..." if len(str(value)) > 100 else "")
                    }
                    
                    # Check if field might be a reference to another collection
                    if field.endswith("Id") or field == "_id":
                        all_fields[field]["possible_reference"] = True
        
        return all_fields
    
    def _identify_relationships(self, collections_info: Dict) -> List[Dict]:
        """Identify potential relationships between collections"""
        relationships = []
        
        # Look for foreign key patterns
        for collection_name, collection_info in collections_info.items():
            schema = collection_info.get("schema", {})
            
            for field, field_info in schema.items():
                # Check if field looks like a reference (ends with "Id" or is "_id")
                if field.endswith("Id") or field == "_id":
                    # Look for collections that might be referenced
                    for other_collection in collections_info.keys():
                        # Skip self-references
                        if other_collection == collection_name:
                            continue
                            
                        # If field is like "userId" and there's a "users" collection
                        potential_collection = field[:-2] + "s"  # Convert "userId" to "users"
                        if potential_collection == other_collection or field == "_id":
                            relationships.append({
                                "from_collection": collection_name,
                                "from_field": field,
                                "to_collection": other_collection,
                                "to_field": "_id",
                                "confidence": "high" if field != "_id" else "medium"
                            })
                            
                # Also check if there are fields that look like arrays of refs
                if "types" in field_info and "list" in field_info["types"]:
                    # If field is like "items" and there's an "items" collection
                    if field in collections_info:
                        relationships.append({
                            "from_collection": collection_name,
                            "from_field": field,
                            "to_collection": field,
                            "to_field": "_id",
                            "confidence": "medium",
                            "type": "array"
                        })
        
        return relationships
    
    def execute_query(self, collection_name: str, query_params: Dict) -> pd.DataFrame:
        """Execute a MongoDB query and return results as a pandas DataFrame
        
        Args:
            collection_name: Name of the collection
            query_params: Dictionary with query parameters:
                          - query: MongoDB query filter
                          - projection: Fields to include/exclude
                          - limit: Maximum number of results
                          - sort: Sort specification
                          
        Returns:
            pandas.DataFrame: Query results
        """
        query = query_params.get("query", {})
        limit = query_params.get("limit", 100)
        sort = query_params.get("sort")
        projection = query_params.get("projection")
        
        results = self.db_client.find_many(
            collection_name,
            query=query,
            projection=projection,
            sort=sort,
            limit=limit
        )
        
        # Convert to DataFrame
        if results:
            df = pd.DataFrame(results)
        else:
            # Return empty DataFrame with expected schema
            df = pd.DataFrame()
            
        return df
    
    def execute_aggregation(self, collection_name: str, pipeline: List[Dict]) -> pd.DataFrame:
        """Execute a MongoDB aggregation pipeline and return results as a pandas DataFrame
        
        Args:
            collection_name: Name of the collection
            pipeline: MongoDB aggregation pipeline
            
        Returns:
            pandas.DataFrame: Aggregation results
        """
        results = self.db_client.aggregate(collection_name, pipeline)
        
        # Convert to DataFrame
        if results:
            df = pd.DataFrame(results)
        else:
            # Return empty DataFrame
            df = pd.DataFrame()
            
        return df
    
    def generate_notes(self) -> str:
        """Generate readable notes from MongoDB exploration results"""
        notes = []
        
        # Handle empty exploration
        if not self.exploration_notes:
            return "Database has not been explored yet. Call explore_database() first."
        
        # Database overview
        notes.append(f"## MongoDB Database: {self.exploration_notes['database_name']}")
        notes.append(f"Explored on: {self.exploration_notes['timestamp']}")
        notes.append(f"Found {len(self.exploration_notes['collections'])} collections")
        notes.append("")
        
        # Collections summary
        notes.append("## Collections Overview")
        for collection_name, collection_info in self.exploration_notes['collections'].items():
            notes.append(f"### {collection_name}")
            notes.append(f"- Document count: {collection_info['count']}")
            notes.append(f"- Fields: {', '.join(collection_info['schema'].keys())}")
            notes.append("")
        
        # Relationships
        if self.exploration_notes['relationships']:
            notes.append("## Identified Relationships")
            for relation in self.exploration_notes['relationships']:
                notes.append(f"- {relation['from_collection']}.{relation['from_field']} → {relation['to_collection']}.{relation['to_field']} (Confidence: {relation['confidence']})")
            notes.append("")
        
        # Collection details
        notes.append("## Collection Details")
        for collection_name, collection_info in self.exploration_notes['collections'].items():
            notes.append(f"### {collection_name}")
            notes.append("#### Schema")
            
            for field, field_info in collection_info['schema'].items():
                types_str = ", ".join(field_info['types'])
                notes.append(f"- {field}: {types_str}")
                if "sample" in field_info:
                    notes.append(f"  - Sample: {field_info['sample']}")
            
            notes.append("")
            notes.append("#### Sample Document")
            if collection_info['sample_documents']:
                sample_doc = collection_info['sample_documents'][0]
                sample_str = json.dumps(sample_doc, indent=2, default=str)
                # Truncate if too long
                if len(sample_str) > 500:
                    sample_str = sample_str[:500] + "..."
                notes.append(f"```json\n{sample_str}\n```")
            notes.append("")
        
        return "\n".join(notes)
    
    # MongoDB-specific helper methods
    def get_collection_data(self, collection_name: str, query: Dict = None, 
                          limit: int = 100, sort = None) -> List[Dict]:
        """Get raw collection data (MongoDB-specific helper)"""
        if query is None:
            query = {}
            
        return self.db_client.find_many(
            collection_name,
            query=query,
            sort=sort,
            limit=limit
        )