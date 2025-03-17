import re
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from autogen import UserProxyAgent
from bson import json_util

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mongodb_user_proxy')

class MongoDBUserProxy(UserProxyAgent):
    """Enhanced User Proxy agent with direct MongoDB function execution support"""
    
    def __init__(self, mongodb_explorer, **kwargs):
        """Initialize the MongoDB User Proxy agent"""
        # Always add code_execution_config with use_docker: False
        if "code_execution_config" not in kwargs:
            kwargs["code_execution_config"] = {"use_docker": False}
        else:
            # Ensure use_docker is set to False in the existing config
            kwargs["code_execution_config"]["use_docker"] = False
        
        # Set human_input_mode to NEVER if not specified
        if "human_input_mode" not in kwargs:
            kwargs["human_input_mode"] = "NEVER"
            
        logger.info(f"Initializing MongoDBUserProxy with config: {kwargs}")
        
        super().__init__(**kwargs)
        
        self.mongodb_explorer = mongodb_explorer
        self.exploration_notes = None
        
        # Define functions dictionary for execution
        self.mongodb_functions = {
            "explore_mongodb": self.explore_mongodb,
            "get_exploration_notes": self.get_exploration_notes,
            "execute_query": self.execute_query,
            "execute_aggregation": self.execute_aggregation,
            "create_visualization": self.create_visualization,
            "get_collection_sample": self.get_collection_sample,
            "count_documents": self.count_documents,
            "validate_query": self.validate_query,
            "get_distinct_values": self.get_distinct_values,
            "get_connection_status": self.get_connection_status
        }
    
    def generate_reply(self, messages=None, sender=None, config=None):
        """Override generate_reply to handle Python code blocks with MongoDB functions"""
        # Get the latest message
        if not messages:
            return {"content": "No messages to process."}
        
        latest_message = messages[-1]["content"]
        
        # Check if the message contains a Python code block
        if "```python" in latest_message:
            # Extract and execute all Python code blocks
            pattern = r"```python\s*(.*?)\s*```"
            code_blocks = re.findall(pattern, latest_message, re.DOTALL)
            
            if code_blocks:
                modified_message = latest_message
                
                for i, code_block in enumerate(code_blocks):
                    # Execute the code block and get the result
                    result = self._execute_code_block(code_block)
                    logger.info(f"Executed code block {i+1} with result: {result[:100]}...")
                    
                    # Replace the code block with the code + result
                    original_block = f"```python\n{code_block}\n```"
                    replacement = f"```python\n{code_block}\n```\n\n**Execution Results:**\n```\n{result}\n```"
                    modified_message = modified_message.replace(original_block, replacement)
                
                # Return the modified message
                logger.info("Generated reply with executed code blocks")
                return {"content": modified_message}
        
        # Default handler for non-code messages
        logger.info("Using default handler for message without code blocks")
        return super().generate_reply(messages=messages, sender=sender, config=config)
    
    def _execute_code_block(self, code_block: str) -> str:
        """Execute a Python code block with MongoDB functions available
        
        Args:
            code_block: Python code to execute
            
        Returns:
            Execution result as string
        """
        try:
            # Parse the code block to find MongoDB function calls
            result = ""
            
            # Simple parsing for function calls (name and arguments)
            # This is a basic implementation - a more robust parser could be implemented
            lines = code_block.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Try to match a function call pattern: function_name(args)
                match = re.match(r'(\w+)\((.*)\)$', line)
                if match:
                    func_name = match.group(1)
                    args_str = match.group(2)
                    
                    # Check if this is a MongoDB function
                    if func_name in self.mongodb_functions:
                        func_result = self._call_mongodb_function(func_name, args_str)
                        result += f"# Result of {func_name}():\n{func_result}\n\n"
                    else:
                        result += f"# Error: Function '{func_name}' is not a registered MongoDB function\n\n"
                else:
                    # Line is not a function call
                    result += f"# Warning: Could not parse as function call: {line}\n"
            
            if not result:
                result = "# No MongoDB function calls found in code block"
                
            return result
            
        except Exception as e:
            error_msg = f"Error executing code block: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _call_mongodb_function(self, func_name: str, args_str: str) -> str:
        """Call a MongoDB function with parsed arguments
        
        Args:
            func_name: Name of the MongoDB function
            args_str: String representation of function arguments
            
        Returns:
            Function execution result as string
        """
        try:
            # Get the function
            func = self.mongodb_functions[func_name]
            
            # Parse arguments
            args, kwargs = self._parse_arguments(args_str)
            
            # Call the function
            logger.info(f"Calling MongoDB function: {func_name} with args: {args}, kwargs: {kwargs}")
            result = func(*args, **kwargs)
            
            return result
        except Exception as e:
            error_msg = f"Error calling MongoDB function '{func_name}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _parse_arguments(self, args_str: str) -> tuple:
        """Parse function arguments from string
        
        Args:
            args_str: String representation of function arguments
            
        Returns:
            Tuple of (positional_args, keyword_args)
        """
        if not args_str.strip():
            return [], {}
        
        # Split by commas, but respect quotes and nested structures
        # This is a simple implementation - a more robust parser could be implemented
        args = []
        kwargs = {}
        
        # Replace any None with Python None
        args_str = args_str.replace("None", "None")
        
        # Handle keyword arguments
        if '=' in args_str:
            # Split by commas, but not inside quotes or brackets
            parts = []
            current = ""
            in_quotes = False
            quote_char = None
            bracket_level = 0
            
            for char in args_str:
                if char in ['"', "'"]:
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                
                if char == '{':
                    bracket_level += 1
                elif char == '}':
                    bracket_level -= 1
                
                if char == ',' and not in_quotes and bracket_level == 0:
                    parts.append(current)
                    current = ""
                else:
                    current += char
            
            if current:
                parts.append(current)
            
            # Process each part
            for part in parts:
                part = part.strip()
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle different value types
                    if value == "None":
                        kwargs[key] = None
                    elif value.lower() == "true":
                        kwargs[key] = True
                    elif value.lower() == "false":
                        kwargs[key] = False
                    elif value.isdigit():
                        kwargs[key] = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        kwargs[key] = float(value)
                    elif (value.startswith('"') and value.endswith('"')) or \
                         (value.startswith("'") and value.endswith("'")):
                        kwargs[key] = value[1:-1]  # Remove quotes
                    elif value.startswith('{') and value.endswith('}'):
                        # Try to parse as JSON
                        try:
                            kwargs[key] = json.loads(value)
                        except:
                            kwargs[key] = value
                    else:
                        kwargs[key] = value
                else:
                    # Handle positional argument
                    if part == "None":
                        args.append(None)
                    elif part.lower() == "true":
                        args.append(True)
                    elif part.lower() == "false":
                        args.append(False)
                    elif part.isdigit():
                        args.append(int(part))
                    elif part.replace('.', '', 1).isdigit():
                        args.append(float(part))
                    elif (part.startswith('"') and part.endswith('"')) or \
                         (part.startswith("'") and part.endswith("'")):
                        args.append(part[1:-1])  # Remove quotes
                    else:
                        args.append(part)
        else:
            # No keyword arguments, just positional
            for part in args_str.split(','):
                part = part.strip()
                if not part:
                    continue
                    
                if part == "None":
                    args.append(None)
                elif part.lower() == "true":
                    args.append(True)
                elif part.lower() == "false":
                    args.append(False)
                elif part.isdigit():
                    args.append(int(part))
                elif part.replace('.', '', 1).isdigit():
                    args.append(float(part))
                elif (part.startswith('"') and part.endswith('"')) or \
                     (part.startswith("'") and part.endswith("'")):
                    args.append(part[1:-1])  # Remove quotes
                else:
                    args.append(part)
        
        return args, kwargs
    
    #############################################################
    # MongoDB Function Implementations
    #############################################################
    
    def explore_mongodb(self) -> str:
        """Explore the MongoDB database and return notes"""
        try:
            logger.info("Executing explore_mongodb function")
            exploration_results = self.mongodb_explorer.explore_database()
            self.exploration_notes = self.mongodb_explorer.generate_notes()
            
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
            if not self.exploration_notes:
                return "MongoDB database has not been explored yet. Call explore_mongodb() first."
            
            logger.info(f"Returning exploration notes: {self.exploration_notes[:100]}...")
            return self.exploration_notes
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
            collections = self.mongodb_explorer.db_client.list_collections()
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
            df = self.mongodb_explorer.execute_query(collection_name, query_params)
            
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
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Convert string representation to appropriate format if needed
            if isinstance(aggregation_pipeline, str):
                try:
                    aggregation_pipeline = json.loads(aggregation_pipeline)
                except json.JSONDecodeError:
                    return "Error: Invalid aggregation pipeline JSON format."
            
            # Validate pipeline is a list
            if not isinstance(aggregation_pipeline, list):
                return "Error: MongoDB aggregation pipeline must be an array of stages."
            
            # Execute the aggregation
            df = self.mongodb_explorer.execute_aggregation(collection_name, aggregation_pipeline)
            
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
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Get sample documents
            samples = self.mongodb_explorer.db_client.find_many(
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
            collections = self.mongodb_explorer.db_client.list_collections()
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
            count = self.mongodb_explorer.db_client.count_documents(collection_name, query)
            
            # Return formatted result
            filter_str = "" if not query or query == {} else f" matching query {json.dumps(query)}"
            return f"Collection '{collection_name}' contains {count} documents{filter_str}."
        except Exception as e:
            error_msg = f"Error counting documents: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def validate_query(self, collection_name: str, query: Any) -> str:
        """Validate a MongoDB query without executing it"""
        try:
            logger.info(f"Validating query for collection: {collection_name}")
            
            # Check if collection exists
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist in the database."
            
            # Convert string representation of query to dict if needed
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except json.JSONDecodeError:
                    return "Error: Invalid query JSON format. The query could not be parsed."
            
            if not isinstance(query, dict):
                return "Error: Query must be a dictionary (JSON object)."
            
            # Check for valid MongoDB operators
            invalid_operators = []
            for key in query.keys():
                if key.startswith('$') and key not in [
                    '$eq', '$gt', '$gte', '$lt', '$lte', '$ne', '$in', '$nin', 
                    '$and', '$or', '$not', '$nor', '$exists', '$type', '$regex',
                    '$text', '$where', '$expr', '$jsonSchema', '$mod', '$elemMatch'
                ]:
                    invalid_operators.append(key)
            
            if invalid_operators:
                return f"Error: Query contains invalid MongoDB operators: {', '.join(invalid_operators)}"
            
            return "Query validation successful. The query appears to be valid MongoDB syntax."
        except Exception as e:
            error_msg = f"Error validating query: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_distinct_values(self, collection_name: str, field: str, query: Any = None) -> str:
        """Get distinct values for a field in a collection"""
        try:
            logger.info(f"Getting distinct values for field '{field}' in collection: {collection_name}")
            
            # Check collection exists
            collections = self.mongodb_explorer.db_client.list_collections()
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
            values = self.mongodb_explorer.db_client.distinct(collection_name, field, query)
            
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
            is_connected = self.mongodb_explorer.db_client.ping()
            
            if is_connected:
                # Get database stats
                stats = self.mongodb_explorer.db_client.get_database_stats()
                
                db_name = self.mongodb_explorer.db_client.db.name
                collections = len(self.mongodb_explorer.db_client.list_collections())
                
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