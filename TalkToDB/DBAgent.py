"""
Custom MongoDB Agent System

This module provides a custom implementation of a MongoDB agent system that doesn't
rely on Autogen's UserProxyAgent or Docker. It's designed to work with the existing
Streamlit UI implementation.
"""

import os
import re
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

import autogen
from autogen import AssistantAgent
from bson import json_util
import pandas as pd

from mongoDBExplorer import MongoDBExplorer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mongodb_agent')

class MongoDBAgent:
    """MongoDB specialist agent that doesn't require Docker"""
    
    def __init__(self, name: str, system_message: str, openai_model: str, openai_key: str):
        """Initialize a MongoDB agent"""
        self.name = name
        self.system_message = system_message
        
        # Create LLM config
        self.llm_config = {
            "model": openai_model,
            "api_key": openai_key
        }
        
        # Create the assistant agent (only for LLM calls, not execution)
        self.assistant = AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config=self.llm_config
        )
    
    def generate_response(self, messages: List[Dict]) -> str:
        """Generate a response based on messages"""
        try:
            # Generate a response using the assistant
            response = self.assistant.generate_reply(messages)
            
            # Extract content from the response
            if isinstance(response, dict) and "content" in response:
                return response["content"]
            elif isinstance(response, str):
                return response
            else:
                return "Error: Unexpected response format"
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

class MongoDBFunctionHandler:
    """Handle MongoDB function calls"""
    
    def __init__(self, mongodb_explorer: MongoDBExplorer):
        """Initialize with a MongoDB explorer"""
        self.mongodb_explorer = mongodb_explorer
        self.exploration_notes = None
    
    def execute_function(self, function_name: str, *args, **kwargs) -> str:
        """Execute a MongoDB function"""
        # Check if we have this function
        method_name = f"_{function_name}"
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            try:
                # Call the function
                method = getattr(self, method_name)
                return method(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error executing function {function_name}: {str(e)}")
                return f"Error executing {function_name}: {str(e)}"
        else:
            return f"Unknown function: {function_name}"
    
    def _explore_mongodb(self) -> str:
        """Explore the MongoDB database"""
        try:
            logger.info("Executing explore_mongodb")
            
            # Explore the database
            exploration_results = self.mongodb_explorer.explore_database()
            self.exploration_notes = self.mongodb_explorer.generate_notes()
            
            # Format the results
            collection_count = len(exploration_results.get("collections", {}))
            
            collection_info = []
            for coll_name, coll_data in exploration_results.get("collections", {}).items():
                doc_count = coll_data.get("count", 0)
                collection_info.append(f"- {coll_name}: {doc_count} documents")
            
            summary = "\n".join(collection_info)
            return f"MongoDB exploration completed. Found {collection_count} collections:\n{summary}"
            
        except Exception as e:
            logger.error(f"Error in explore_mongodb: {str(e)}")
            return f"Error exploring MongoDB database: {str(e)}"
    
    def _get_exploration_notes(self) -> str:
        """Get detailed exploration notes"""
        try:
            logger.info("Executing get_exploration_notes")
            
            if not self.exploration_notes:
                return "MongoDB database has not been explored yet. Call explore_mongodb() first."
                
            return self.exploration_notes
            
        except Exception as e:
            logger.error(f"Error in get_exploration_notes: {str(e)}")
            return f"Error getting exploration notes: {str(e)}"
    
    def _execute_query(self, collection_name, query=None, limit=100, sort=None, projection=None) -> str:
        """Execute a MongoDB query"""
        try:
            logger.info(f"Executing query on collection: {collection_name}")
            
            # Check if collection exists
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist."
            
            # Parse query if it's a string
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except:
                    return "Error: Invalid query JSON format."
            
            # Default query
            if query is None:
                query = {}
            
            # Build query parameters
            query_params = {
                "query": query,
                "limit": limit,
                "sort": sort,
                "projection": projection
            }
            
            # Execute the query
            df = self.mongodb_explorer.execute_query(collection_name, query_params)
            
            # Format results
            if df.empty:
                return "Query returned no results."
                
            results = f"Query returned {len(df)} documents.\n"
            results += df.head(10).to_string()
            
            if len(df) > 10:
                results += f"\n... and {len(df) - 10} more documents"
                
            return results
            
        except Exception as e:
            logger.error(f"Error in execute_query: {str(e)}")
            return f"Error executing MongoDB query: {str(e)}"
    
    def _execute_aggregation(self, collection_name, aggregation_pipeline) -> str:
        """Execute a MongoDB aggregation pipeline"""
        try:
            logger.info(f"Executing aggregation on collection: {collection_name}")
            
            # Check if collection exists
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist."
            
            # Parse pipeline if it's a string
            if isinstance(aggregation_pipeline, str):
                try:
                    aggregation_pipeline = json.loads(aggregation_pipeline)
                except:
                    return "Error: Invalid aggregation pipeline JSON format."
            
            # Execute the aggregation
            df = self.mongodb_explorer.execute_aggregation(collection_name, aggregation_pipeline)
            
            # Format results
            if df.empty:
                return "Aggregation returned no results."
                
            results = f"Aggregation returned {len(df)} documents.\n"
            results += df.head(10).to_string()
            
            if len(df) > 10:
                results += f"\n... and {len(df) - 10} more documents"
                
            return results
            
        except Exception as e:
            logger.error(f"Error in execute_aggregation: {str(e)}")
            return f"Error executing MongoDB aggregation: {str(e)}"
    
    def _get_collection_sample(self, collection_name, count=5) -> str:
        """Get a sample of documents from a collection"""
        try:
            logger.info(f"Getting sample from collection: {collection_name}")
            
            # Check if collection exists
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist."
            
            # Get sample documents
            samples = self.mongodb_explorer.db_client.find_many(
                collection_name,
                limit=count,
                sort=[("_id", 1)]
            )
            
            if not samples:
                return f"No documents found in collection '{collection_name}'."
                
            # Format as JSON
            sample_json = json.dumps(samples, indent=2, default=json_util.default)
            return f"Sample of {len(samples)} documents from '{collection_name}':\n{sample_json}"
            
        except Exception as e:
            logger.error(f"Error in get_collection_sample: {str(e)}")
            return f"Error getting collection sample: {str(e)}"
    
    def _count_documents(self, collection_name, query=None) -> str:
        """Count documents in a collection"""
        try:
            logger.info(f"Counting documents in collection: {collection_name}")
            
            # Check if collection exists
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist."
            
            # Parse query if it's a string
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except:
                    return "Error: Invalid query JSON format."
            
            # Default query
            if query is None:
                query = {}
                
            # Count documents
            count = self.mongodb_explorer.db_client.count_documents(collection_name, query)
            
            # Format result
            filter_str = "" if not query or query == {} else f" matching query {json.dumps(query)}"
            return f"Collection '{collection_name}' contains {count} documents{filter_str}."
            
        except Exception as e:
            logger.error(f"Error in count_documents: {str(e)}")
            return f"Error counting documents: {str(e)}"
    
    def _get_distinct_values(self, collection_name, field, query=None) -> str:
        """Get distinct values for a field"""
        try:
            logger.info(f"Getting distinct values for field: {field}")
            
            # Check if collection exists
            collections = self.mongodb_explorer.db_client.list_collections()
            if collection_name not in collections:
                return f"Error: Collection '{collection_name}' does not exist."
            
            # Parse query if it's a string
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except:
                    return "Error: Invalid query JSON format."
            
            # Default query
            if query is None:
                query = {}
                
            # Get distinct values
            values = self.mongodb_explorer.db_client.distinct(collection_name, field, query)
            
            # Format result
            if not values:
                return f"No distinct values found for field '{field}'."
                
            # Limit display if there are too many values
            display_limit = 50
            display_values = values[:display_limit]
            extra_count = len(values) - display_limit if len(values) > display_limit else 0
            
            # Format as JSON
            values_str = json.dumps(display_values, default=json_util.default)
            
            result = f"Found {len(values)} distinct values for field '{field}'.\n"
            result += f"Values: {values_str}"
            
            if extra_count > 0:
                result += f"\n... and {extra_count} more values"
                
            return result
            
        except Exception as e:
            logger.error(f"Error in get_distinct_values: {str(e)}")
            return f"Error getting distinct values: {str(e)}"
    
    def _get_connection_status(self) -> str:
        """Check the MongoDB connection status"""
        try:
            logger.info("Checking connection status")
            
            # Check connection
            is_connected = self.mongodb_explorer.db_client.ping()
            
            if is_connected:
                # Get database info
                db_name = self.mongodb_explorer.db_client.db.name
                stats = self.mongodb_explorer.db_client.get_database_stats()
                collections = len(self.mongodb_explorer.db_client.list_collections())
                
                return (
                    f"✅ Connected to MongoDB database: {db_name}\n"
                    f"Collections: {collections}\n"
                    f"Storage size: {stats.get('storageSize', 'unknown')} bytes\n"
                    f"Objects: {stats.get('objects', 'unknown')}\n"
                    f"Indexes: {stats.get('indexes', 'unknown')}"
                )
            else:
                return "❌ Not connected to MongoDB."
                
        except Exception as e:
            logger.error(f"Error in get_connection_status: {str(e)}")
            return f"Error checking connection: {str(e)}"
    
    def _create_visualization(self, collection_name, viz_type, params=None, query=None) -> str:
        """Create a visualization (placeholder)"""
        return "Visualization creation is handled by the UI layer."


class CodeBlockProcessor:
    """Process Python code blocks to extract and execute MongoDB functions"""
    
    def __init__(self, function_handler: MongoDBFunctionHandler):
        """Initialize with a function handler"""
        self.function_handler = function_handler
    
    def process_code_blocks(self, message: str) -> str:
        """Process all Python code blocks in a message"""
        # Find all Python code blocks
        pattern = r"```python\s*(.*?)\s*```"
        code_blocks = re.findall(pattern, message, re.DOTALL)
        
        if not code_blocks:
            return message
            
        # Process each code block
        modified_message = message
        for code_block in code_blocks:
            # Execute the code block
            result = self._execute_code_block(code_block)
            
            # Replace the code block with the result
            original = f"```python\n{code_block}\n```"
            replacement = f"```python\n{code_block}\n```\n\n**Execution Results:**\n```\n{result}\n```"
            modified_message = modified_message.replace(original, replacement)
            
        return modified_message
    
    def _execute_code_block(self, code_block: str) -> str:
        """Execute a Python code block with MongoDB functions"""
        results = []
        
        # Split the code block into lines
        lines = code_block.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
                
            # Try to match function calls
            match = re.match(r'(\w+)\((.*)\)', line)
            if not match:
                results.append(f"# Warning: Could not parse: {line}")
                continue
                
            function_name = match.group(1)
            args_str = match.group(2)
            
            # Parse arguments and call the function
            args, kwargs = self._parse_arguments(args_str)
            result = self.function_handler.execute_function(function_name, *args, **kwargs)
            
            # Add the result
            results.append(f"# Result of {function_name}():\n{result}")
        
        return "\n\n".join(results) if results else "# No MongoDB functions were executed"
    
    def _parse_arguments(self, args_str: str) -> tuple:
        """Parse function arguments from a string"""
        args = []
        kwargs = {}
        
        if not args_str.strip():
            return args, kwargs
            
        # Split by commas, but respect quotes and nested structures
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
            if not part:
                continue
                
            if '=' in part:
                # Keyword argument
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                kwargs[key] = self._parse_value(value)
            else:
                # Positional argument
                args.append(self._parse_value(part))
        
        return args, kwargs
    
    def _parse_value(self, value: str) -> Any:
        """Parse a value string into the appropriate Python type"""
        # None
        if value == "None":
            return None
            
        # Boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
            
        # Number
        if value.isdigit():
            return int(value)
        if value.replace('.', '', 1).isdigit():
            return float(value)
            
        # String
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
            
        # JSON object
        if value.startswith('{') and value.endswith('}'):
            try:
                # Replace single quotes with double quotes for JSON parsing
                json_str = value.replace("'", '"')
                return json.loads(json_str)
            except:
                pass
                
        # JSON array
        if value.startswith('[') and value.endswith(']'):
            try:
                # Replace single quotes with double quotes for JSON parsing
                json_str = value.replace("'", '"')
                return json.loads(json_str)
            except:
                pass
                
        # Default to the original value
        return value


class MongoDBConversation:
    """Manage a conversation with MongoDB agents"""
    
    def __init__(self, agents: Dict[str, MongoDBAgent], function_handler: MongoDBFunctionHandler):
        """Initialize with agents and a function handler"""
        self.agents = agents
        self.function_handler = function_handler
        self.code_processor = CodeBlockProcessor(function_handler)
        self.messages = []
        self.listeners = []
    
    def add_message(self, role: str, content: str, agent_name: str = None) -> Dict:
        """Add a message to the conversation"""
        message = {
            "role": role,
            "content": content,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        
        if agent_name:
            message["agent"] = agent_name
            
        self.messages.append(message)
        return message
    
    def add_response_listener(self, listener) -> None:
        """Add a response listener"""
        self.listeners.append(listener)
        logger.info(f"Added response listener: {type(listener).__name__}")
    
    def notify_listeners(self, agent_name: str, message: str, metadata: Dict = None) -> None:
        """Notify all listeners of a new response"""
        logger.info(f"Notifying listeners of response from {agent_name}")
        
        for listener in self.listeners:
            if hasattr(listener, 'on_response'):
                listener.on_response(agent_name, message, metadata)
            elif hasattr(listener, 'capture_response'):
                listener.capture_response(agent_name, message, metadata)
            elif callable(listener):
                listener(agent_name, message, metadata)
    
    def process_user_message(self, message: str) -> List[Dict]:
        """Process a user message and generate responses"""
        # Add the user message
        self.add_message("user", message)
        
        # Format the message for the LLM
        formatted_messages = []
        for msg in self.messages:
            formatted_messages.append({
                "role": "system" if msg.get("agent") else msg["role"],
                "content": msg["content"],
                "name": msg.get("agent") if msg.get("agent") else None
            })
        
        # Choose which agent should respond
        responses = []
        
        # Always start with the explorer agent
        explorer_agent = self.agents["MongoDBExplorer"]
        explorer_response = explorer_agent.generate_response(formatted_messages)
        
        # Check if the response contains code blocks
        if "```python" in explorer_response:
            # Process code blocks
            processed_response = self.code_processor.process_code_blocks(explorer_response)
            
            # Add the response
            response = self.add_message("assistant", processed_response, "MongoDBExplorer")
            responses.append(response)
            
            # Notify listeners
            self.notify_listeners("MongoDBExplorer", processed_response)
            
            # If no MongoDB functions were executed, try the query specialist
            if "# No MongoDB functions were executed" in processed_response or "# Warning: Could not parse" in processed_response:
                query_agent = self.agents["MongoDBQuerySpecialist"]
                query_response = query_agent.generate_response(formatted_messages + [{"role": "system", "content": processed_response, "name": "MongoDBExplorer"}])
                
                # Process code blocks
                processed_query_response = self.code_processor.process_code_blocks(query_response)
                
                # Add the response
                query_msg = self.add_message("assistant", processed_query_response, "MongoDBQuerySpecialist")
                responses.append(query_msg)
                
                # Notify listeners
                self.notify_listeners("MongoDBQuerySpecialist", processed_query_response)
        else:
            # No code blocks, just add the response
            response = self.add_message("assistant", explorer_response, "MongoDBExplorer")
            responses.append(response)
            
            # Notify listeners
            self.notify_listeners("MongoDBExplorer", explorer_response)
        
        return responses


class MongoDBAgentSystem:
    """MongoDB Agent System that doesn't require Docker"""
    
    def __init__(self, connection_string: str, db_name: str, openai_model: str, openai_key: str):
        """Initialize the MongoDB agent system"""
        self.connection_string = connection_string
        self.db_name = db_name
        self.openai_model = openai_model
        self.openai_key = openai_key
        self.response_listeners = []
        
        # Initialize MongoDB explorer
        try:
            self.mongodb_explorer = MongoDBExplorer(db_name=db_name, connection_string=connection_string)
            logger.info(f"Successfully initialized MongoDB explorer for database '{db_name}'")
        except Exception as e:
            error_msg = f"Failed to initialize MongoDB explorer: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        
        # Set up the agent system
        self.setup_agents()
    
    def setup_agents(self):
        """Set up the agent system"""
        # Create function handler
        self.function_handler = MongoDBFunctionHandler(self.mongodb_explorer)
        
        # Create MongoDB agents
        self.agents = {
            "MongoDBExplorer": MongoDBAgent(
                name="MongoDBExplorer",
                system_message="""You are a MongoDB database exploration specialist.
Your role is to understand MongoDB database structure, schema, and relationships.

When analyzing a MongoDB database, use these functions in Python code blocks:

```python
explore_mongodb()
```

```python
get_exploration_notes()
```

```python
get_collection_sample("collection_name")
```

Always start by exploring the database structure with explore_mongodb().
Then get detailed notes with get_exploration_notes().
Examine specific collections with get_collection_sample().

Explain MongoDB concepts in user-friendly terms.
""",
                openai_model=self.openai_model,
                openai_key=self.openai_key
            ),
            "MongoDBQuerySpecialist": MongoDBAgent(
                name="MongoDBQuerySpecialist",
                system_message="""You are a MongoDB query specialist.
Your expertise is in writing efficient, correct MongoDB queries.

Use these functions in Python code blocks to query MongoDB:

```python
execute_query("collection_name", {"field": "value"})
```

```python
execute_aggregation("collection_name", [{"$match": {"field": "value"}}, {"$group": {...}}])
```

```python
count_documents("collection_name", {"field": "value"})
```

```python
get_distinct_values("collection_name", "field_name")
```

Use proper MongoDB query syntax with correct operators like $eq, $gt, $in, etc.
For complex queries, use aggregation pipelines with stages like $match, $group, $sort.
""",
                openai_model=self.openai_model,
                openai_key=self.openai_key
            ),
            "MongoDBVisualizationSpecialist": MongoDBAgent(
                name="MongoDBVisualizationSpecialist",
                system_message="""You are a MongoDB data visualization specialist.
Your expertise is in creating effective visualizations from MongoDB data.

Use these functions in Python code blocks for data visualization:

```python
execute_query("collection_name", {"status": "active"})
```

```python
create_visualization("collection_name", "bar", params={"x": "field1", "y": "field2"})
```

Choose appropriate visualization types based on the data:
- bar charts for comparing categories
- line charts for trends over time
- scatter plots for relationships
- pie charts for composition
- histograms for distributions

Make sure to add appropriate titles and labels to visualizations.
""",
                openai_model=self.openai_model,
                openai_key=self.openai_key
            )
        }
        
        # Create conversation manager
        self.conversation = MongoDBConversation(self.agents, self.function_handler)
    
    def add_response_listener(self, listener):
        """Add a response listener"""
        self.conversation.add_response_listener(listener)
    
    def start_interaction(self, message: str):
        """Start an interaction with the MongoDB agent system"""
        if message is None:
            message = "I need help analyzing my MongoDB database."
        
        try:
            # Process the message
            responses = self.conversation.process_user_message(message)
            
            # Return all responses
            return responses
        except Exception as e:
            error_msg = f"Error starting interaction: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)