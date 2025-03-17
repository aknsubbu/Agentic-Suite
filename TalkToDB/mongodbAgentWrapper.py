"""
MongoDB Agent Wrapper

This file provides a wrapper around the MongoDB Agent System to ensure
proper function execution within the Autogen framework.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import inspect
import functools

import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
from bson import json_util

from mongoDBExplorer import MongoDBExplorer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mongodb_wrapper')

class MongoDBAgentWrapper:
    """Wrapper around MongoDB agents to ensure proper function execution"""
    
    def __init__(self, db_explorer):
        """Initialize with a MongoDB explorer"""
        self.db_explorer = db_explorer
        self.functions = {}
        self._register_functions()
    
    def _register_functions(self):
        """Register all MongoDB functions"""
        self.functions = {
            "explore_mongodb": self.explore_mongodb,
            "get_exploration_notes": self.get_exploration_notes,
            "execute_query": self.execute_query,
            "execute_aggregation": self.execute_aggregation,
            "get_collection_sample": self.get_collection_sample,
            "count_documents": self.count_documents,
            "get_distinct_values": self.get_distinct_values,
            "get_connection_status": self.get_connection_status,
            "create_visualization": self.create_visualization
        }
        
        # Register functions in the global scope for code execution
        for name, func in self.functions.items():
            globals()[name] = func
    
    def explore_mongodb(self) -> str:
        """Explore the MongoDB database and return notes"""
        try:
            logger.info("Executing explore_mongodb function")
            exploration_results = self.db_explorer.explore_database()
            
            # Get the number of collections from the results
            collection_count = len(exploration_results.get("collections", {}))
            
            collection_info = []
            for coll_name, coll_data in exploration_results.get("collections", {}).items():
                doc_count = coll_data.get("count", 0)
                collection_info.append(f"- {coll_name}: {doc_count} documents")
            
            summary = "\n".join(collection_info)
            result = f"MongoDB exploration completed. Found {collection_count} collections:\n{summary}"
            logger.info(f"explore_mongodb result: {result[:100]}...")
            return result
        except Exception as e:
            error_msg = f"Error exploring MongoDB database: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_exploration_notes(self) -> str:
        """Get the MongoDB exploration notes"""
        try:
            logger.info("Executing get_exploration_notes function")
            notes = self.db_explorer.generate_notes()
            if not notes:
                return "MongoDB database has not been explored yet. Call explore_mongodb() first."
            
            logger.info(f"Returning exploration notes: {notes[:100]}...")
            return notes
        except Exception as e:
            error_msg = f"Error getting exploration notes: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def execute_query(self, collection_name: str, query: Any = None, 
                     limit: int = 100, sort = None, projection = None) -> str:
        """Execute a MongoDB query and return results"""
        try:
            logger.info(f"Executing query on collection: {collection_name}")
            
            # Check collection exists
            collections = self.db_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Convert string representation of query to dict if needed
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except json.JSONDecodeError:
                    return "Error: Invalid query JSON format. The query could not be parsed."
            
            # Handle None/empty query
            if query is None:
                query = {}
            
            # Convert string representation of sort to list if needed
            if isinstance(sort, str):
                try:
                    sort = json.loads(sort)
                except json.JSONDecodeError:
                    return "Error: Invalid sort JSON format. The sort specification could not be parsed."
            
            # Convert projection if needed
            if isinstance(projection, str):
                try:
                    projection = json.loads(projection)
                except json.JSONDecodeError:
                    return "Error: Invalid projection JSON format."
            
            # Build query params
            query_params = {
                "query": query,
                "limit": limit,
                "sort": sort,
                "projection": projection
            }
            
            # Execute the query
            df = self.db_explorer.execute_query(collection_name, query_params)
            
            # Return results
            if df.empty:
                return "Query returned no results."
            
            # Format the results
            results_str = f"Query returned {len(df)} documents.\n"
            
            # Handle ObjectId and other MongoDB-specific types for display
            import pandas as pd
            pd.set_option('display.max_colwidth', 30)
            
            # Format the DataFrame for display
            results_str += df.head(10).to_string()
            
            if len(df) > 10:
                results_str += f"\n... and {len(df) - 10} more documents"
                
            return results_str
        except Exception as e:
            error_msg = f"Error executing MongoDB query: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def execute_aggregation(self, collection_name: str, aggregation_pipeline: Any) -> str:
        """Execute a MongoDB aggregation pipeline and return results"""
        try:
            logger.info(f"Executing aggregation on collection: {collection_name}")
            
            # Check collection exists
            collections = self.db_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Convert string representation to appropriate format if needed
            if isinstance(aggregation_pipeline, str):
                try:
                    aggregation_pipeline = json.loads(aggregation_pipeline)
                except json.JSONDecodeError:
                    return "Error: Invalid aggregation pipeline JSON format."
            
            # Execute the aggregation
            df = self.db_explorer.execute_aggregation(collection_name, aggregation_pipeline)
            
            # Return results
            if df.empty:
                return "Aggregation returned no results."
            
            # Format the results
            results_str = f"Aggregation returned {len(df)} documents.\n"
            
            # Format the DataFrame for display
            import pandas as pd
            pd.set_option('display.max_colwidth', 30)
            results_str += df.head(10).to_string()
            
            if len(df) > 10:
                results_str += f"\n... and {len(df) - 10} more documents"
                
            return results_str
        except Exception as e:
            error_msg = f"Error executing MongoDB aggregation: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_collection_sample(self, collection_name: str, count: int = 5) -> str:
        """Get a sample of documents from a collection"""
        try:
            logger.info(f"Getting sample from collection: {collection_name}")
            
            # Check collection exists
            collections = self.db_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Get sample documents
            samples = self.db_explorer.db_client.find_many(
                collection_name, 
                limit=count,
                sort=[("_id", 1)]
            )
            
            if not samples:
                return f"No documents found in collection '{collection_name}'."
            
            # Format samples as readable JSON
            sample_json = json.dumps(samples, indent=2, default=json_util.default)
            
            return f"Sample of {len(samples)} documents from '{collection_name}':\n{sample_json}"
        except Exception as e:
            error_msg = f"Error retrieving collection sample: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def count_documents(self, collection_name: str, query: Any = None) -> str:
        """Count documents in a collection, optionally filtered by a query"""
        try:
            logger.info(f"Counting documents in collection: {collection_name}")
            
            # Check collection exists
            collections = self.db_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Convert string representation of query to dict if needed
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except json.JSONDecodeError:
                    return "Error: Invalid query JSON format"
            
            # Handle None query
            if query is None:
                query = {}
                
            # Count documents
            count = self.db_explorer.db_client.count_documents(collection_name, query)
            
            # Return formatted result
            filter_str = "" if not query or query == {} else f" matching query {json.dumps(query)}"
            return f"Collection '{collection_name}' contains {count} documents{filter_str}."
        except Exception as e:
            error_msg = f"Error counting documents: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_distinct_values(self, collection_name: str, field: str, query: Any = None) -> str:
        """Get distinct values for a field in a collection"""
        try:
            logger.info(f"Getting distinct values for field '{field}' in collection: {collection_name}")
            
            # Check collection exists
            collections = self.db_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Convert string representation of query to dict if needed
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except json.JSONDecodeError:
                    return "Error: Invalid query JSON format"
            
            # Handle None query
            if query is None:
                query = {}
                
            # Get distinct values
            values = self.db_explorer.db_client.distinct(collection_name, field, query)
            
            # Format output
            if not values:
                return f"No distinct values found for field '{field}' in collection '{collection_name}'."
            
            # Limit number of displayed values if too many
            display_limit = 50
            display_values = values[:display_limit]
            additional_count = len(values) - display_limit if len(values) > display_limit else 0
            
            # Format values as string
            values_str = json.dumps(display_values, default=json_util.default)
            
            result = f"Found {len(values)} distinct values for field '{field}' in collection '{collection_name}'.\n"
            result += f"Values: {values_str}"
            
            if additional_count > 0:
                result += f"\n... and {additional_count} more values"
                
            return result
        except Exception as e:
            error_msg = f"Error getting distinct values: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_connection_status(self) -> str:
        """Check MongoDB connection status"""
        try:
            logger.info("Checking MongoDB connection status")
            
            # Test the connection
            is_connected = self.db_explorer.db_client.ping()
            
            if is_connected:
                # Get database stats
                stats = self.db_explorer.db_client.get_database_stats()
                
                db_name = self.db_explorer.db_client.db.name
                collections = len(self.db_explorer.db_client.list_collections())
                
                return (
                    f"✅ Connected to MongoDB database: {db_name}\n"
                    f"Collections: {collections}\n"
                    f"Storage size: {stats.get('storageSize', 'unknown')} bytes\n"
                    f"Objects: {stats.get('objects', 'unknown')}\n"
                    f"Indexes: {stats.get('indexes', 'unknown')}"
                )
            else:
                return "❌ Not connected to MongoDB. Check connection parameters."
        except Exception as e:
            error_msg = f"Error checking connection status: {str(e)}"
            logger.error(error_msg)
            return f"❌ MongoDB connection error: {str(e)}"
    
    def create_visualization(self, collection_name: str, viz_type: str, 
                           query: Any = None, params: Dict = None, 
                           output_path: str = None, 
                           aggregation_pipeline: List = None) -> str:
        """Create a visualization from MongoDB data"""
        logger.info(f"Creating {viz_type} visualization for collection: {collection_name}")
        return "Visualization functionality is handled by the UI. This is a placeholder function."

class MongoDBAgentSystem:
    """MongoDB-specific agent system that uses the wrapper for function execution"""
    
    def __init__(self, connection_string: str, db_name: str, openai_model: str, openai_key: str):
        """Initialize the MongoDB agent system"""
        self.connection_string = connection_string
        self.db_name = db_name
        self.openai_model = openai_model
        self.openai_key = openai_key
        self.response_listeners = []
        
        # Initialize MongoDB explorer
        from mongoDBExplorer import MongoDBExplorer
        self.mongodb_explorer = MongoDBExplorer(db_name=db_name, connection_string=connection_string)
        
        # Initialize wrapper
        self.wrapper = MongoDBAgentWrapper(self.mongodb_explorer)
        
        # Set up the agents
        self.setup_agents()
    
    def setup_agents(self):
        """Set up the specialized agents for MongoDB analysis"""
        
        # Define a code execution function that uses our wrapper
        def execute_code(code):
            """Execute code with access to MongoDB functions"""
            try:
                # Add MongoDB functions to the global scope
                globals().update(self.wrapper.functions)
                
                # Execute the code
                exec_locals = {}
                exec(code, globals(), exec_locals)
                
                # Return any result
                if '_result' in exec_locals:
                    return exec_locals['_result']
                return "Code executed successfully."
            except Exception as e:
                return f"Error executing code: {str(e)}"
        
        # Create a user proxy agent with the execute_code function
        self.user_proxy = UserProxyAgent(
            name="MongoDBUserProxy",
            human_input_mode="NEVER",
            code_execution_config={
                "executor": execute_code,
                "last_n_messages": 3,
                "work_dir": "."
            }
        )
        
        # Create a MongoDB explorer assistant
        self.mongodb_explorer_agent = AssistantAgent(
            name="MongoDBExplorer",
            llm_config={
                "model": self.openai_model,
                "api_key": self.openai_key,
                "temperature": 0.1
            },
            system_message="""You are a MongoDB database exploration specialist.
Your role is to understand MongoDB database structure, schema, and relationships.

When analyzing MongoDB databases, you can use these functions:
- explore_mongodb() - Explore the database structure
- get_exploration_notes() - Get detailed notes about the database
- get_collection_sample(collection_name, count) - Get sample documents
- count_documents(collection_name, query) - Count documents in a collection

When you need to use these functions, wrap them in a Python code block like this:
```python
result = explore_mongodb()
print(result)
```

Always start exploration with explore_mongodb() followed by get_exploration_notes().
Explain MongoDB concepts in clear, user-friendly terms.
"""
        )
        
        # Create a MongoDB query specialist
        self.query_specialist = AssistantAgent(
            name="MongoDBQuerySpecialist",
            llm_config={
                "model": self.openai_model,
                "api_key": self.openai_key,
                "temperature": 0.2
            },
            system_message="""You are a MongoDB query specialist.
Your expertise is in writing efficient, correct MongoDB queries.

When querying MongoDB, you can use these functions:
- execute_query(collection_name, query, limit, sort, projection) - Execute a query
- execute_aggregation(collection_name, pipeline) - Execute an aggregation
- count_documents(collection_name, query) - Count documents
- get_distinct_values(collection_name, field, query) - Get distinct values

When you need to use these functions, wrap them in a Python code block like this:
```python
result = execute_query("users", {"status": "active"}, limit=10)
print(result)
```

Use proper MongoDB query syntax for the query parameter.
For aggregations, use proper MongoDB aggregation pipeline stages.
"""
        )
        
        # Create a MongoDB visualization specialist
        self.viz_specialist = AssistantAgent(
            name="MongoDBVisualizationSpecialist",
            llm_config={
                "model": self.openai_model,
                "api_key": self.openai_key,
                "temperature": 0.3
            },
            system_message="""You are a MongoDB data visualization specialist.
Your expertise is in creating effective visualizations for MongoDB data.

When creating visualizations, you can use:
- execute_query(collection_name, query, limit) - Get data to visualize
- execute_aggregation(collection_name, pipeline) - Get aggregated data
- create_visualization(collection_name, viz_type, query, params) - Create a visualization

Supported visualization types:
- bar: For categories (params: x, y)
- line: For trends (params: x, y)
- scatter: For relationships (params: x, y)
- pie: For composition (params: names, values)
- histogram: For distribution (params: x)

When you need to use these functions, wrap them in a Python code block like this:
```python
data = execute_query("orders", {"status": "completed"})
print(data)
viz = create_visualization("orders", "bar", params={"x": "category", "y": "count"})
print(viz)
```

Choose appropriate visualization types based on the data and question.
"""
        )
        
        # Create the group chat
        self.group_chat = GroupChat(
            agents=[
                self.user_proxy,
                self.mongodb_explorer_agent,
                self.query_specialist,
                self.viz_specialist
            ],
            messages=[]
        )
        
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config={
                "model": self.openai_model,
                "api_key": self.openai_key,
                "temperature": 0.2
            }
        )
    
    def add_response_listener(self, listener):
        """Add a response listener"""
        self.response_listeners.append(listener)
    
    def notify_listeners(self, agent_name, message, metadata=None):
        """Notify all listeners of a new response"""
        for listener in self.response_listeners:
            if hasattr(listener, 'on_response'):
                listener.on_response(agent_name, message, metadata)
            else:
                listener(agent_name, message, metadata)
    
    def start_interaction(self, message):
        """Start an interaction with the agent system"""
        try:
            # Make sure MongoDB functions are in the global scope
            globals().update(self.wrapper.functions)
            
            # Start the chat with properly formed message
            return self.user_proxy.initiate_chat(
                recipient=self.manager,
                message=message
            )
        except Exception as e:
            logger.error(f"Error in start_interaction: {str(e)}")
            raise Exception(f"Error starting interaction: {str(e)}")