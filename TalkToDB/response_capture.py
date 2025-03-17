"""
MongoDB Response Capture System

This file contains classes for capturing responses from the MongoDB agent system
to display in the Streamlit UI. It's specifically designed to work with the
MongoDBAgentSystem implementation.
"""

from typing import Dict, List, Any, Callable, Optional
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import logging
import traceback
from bson import json_util
import json
import types

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mongodb_response_capture')

class ResponseListener:
    """Interface for objects that listen to MongoDB agent responses"""
    
    def on_response(self, agent_name: str, message: str, metadata: Optional[Dict] = None):
        """Handle a response from a MongoDB agent"""
        pass

class ResponseCapture(ResponseListener):
    """Captures responses from MongoDB agents for use with UI interfaces"""
    
    def __init__(self):
        self.responses = []
        self.latest_response = None
        logger.info("MongoDB ResponseCapture initialized")
        
    def on_response(self, agent_name: str, message: str, metadata: Optional[Dict] = None):
        """Capture a response from a MongoDB agent"""
        try:
            # Create the base response object
            response = {
                "agent": agent_name,
                "content": message,
                "role": "assistant",
                "type": "text",
                "time": datetime.now().strftime("%H:%M:%S"),
                "metadata": metadata or {}
            }
            
            # Check if the response contains MongoDB data (table/DataFrame)
            if metadata and "data" in metadata and isinstance(metadata["data"], pd.DataFrame):
                response["type"] = "data"
                response["data"] = metadata["data"]
                
                # Apply MongoDB-specific formatting to the DataFrame if needed
                if "_id" in response["data"].columns:
                    # Ensure ObjectId values are properly converted to strings
                    response["data"]["_id"] = response["data"]["_id"].astype(str)
                
                logger.info(f"Captured MongoDB data response from {agent_name} with {len(response['data'])} rows")
            
            # Check if the response contains a MongoDB visualization
            if metadata and "visualization" in metadata and isinstance(metadata["visualization"], go.Figure):
                response["type"] = "visualization"
                response["visualization"] = metadata["visualization"]
                
                # Add MongoDB specific theming to the visualization
                if hasattr(response["visualization"], "update_layout"):
                    response["visualization"].update_layout(
                        template="plotly",
                        title_font=dict(color="#4DB33D"),  # MongoDB green
                        plot_bgcolor="white",
                        paper_bgcolor="white"
                    )
                
                logger.info(f"Captured MongoDB visualization response from {agent_name}")
            
            # Check for MongoDB-specific response types
            if metadata and "mongodb_type" in metadata:
                response["mongodb_type"] = metadata["mongodb_type"]
                logger.info(f"Captured MongoDB-specific response type: {metadata['mongodb_type']}")
            
            # Store the response
            self.responses.append(response)
            self.latest_response = response
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing MongoDB response: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            
            # Create an error response
            error_response = {
                "agent": agent_name,
                "content": f"Error processing response: {str(e)}",
                "role": "assistant",
                "type": "text",
                "time": datetime.now().strftime("%H:%M:%S")
            }
            
            self.responses.append(error_response)
            self.latest_response = error_response
            
            return error_response
    
    # Add an alias for compatibility with existing code
    capture_response = on_response

    def get_conversation_history(self, include_metadata=False):
        """Get the captured conversation history in a format suitable for exporting"""
        try:
            history = []
            
            for response in self.responses:
                # Create a copy without large objects
                response_copy = {
                    "agent": response.get("agent", "System"),
                    "content": response.get("content", ""),
                    "role": response.get("role", "assistant"),
                    "type": response.get("type", "text"),
                    "time": response.get("time", datetime.now().strftime("%H:%M:%S"))
                }
                
                # Optionally include metadata (excluding large objects)
                if include_metadata and "metadata" in response:
                    # Filter out large objects like dataframes and visualizations
                    metadata_copy = {k: v for k, v in response["metadata"].items() 
                                   if k not in ["data", "visualization"]}
                    response_copy["metadata"] = metadata_copy
                
                # Add MongoDB specific type if present
                if "mongodb_type" in response:
                    response_copy["mongodb_type"] = response["mongodb_type"]
                
                history.append(response_copy)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    def export_to_json(self, filepath):
        """Export the conversation history to a JSON file"""
        try:
            history = self.get_conversation_history()
            
            with open(filepath, "w") as f:
                json.dump(history, f, indent=2, default=json_util.default)
                
            logger.info(f"Successfully exported conversation history to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting conversation history: {str(e)}")
            return False
    
    def clear(self):
        """Clear all captured responses"""
        self.responses = []
        self.latest_response = None
        logger.info("Cleared all captured responses")


class MongoDBResponseFormatter:
    """Helper class for formatting MongoDB responses in a user-friendly way"""
    
    @staticmethod
    def format_document(doc, max_length=1000):
        """Format a MongoDB document as a readable string"""
        try:
            # Convert to JSON string with proper handling of MongoDB types
            json_str = json.dumps(doc, indent=2, default=json_util.default)
            
            # Truncate if too long
            if len(json_str) > max_length:
                return json_str[:max_length] + "...\n[Document truncated due to length]"
            
            return json_str
            
        except Exception as e:
            logger.error(f"Error formatting MongoDB document: {str(e)}")
            return str(doc)
    
    @staticmethod
    def format_collection_info(collection_info, include_sample=True):
        """Format collection information in a readable way"""
        try:
            result = []
            
            # Basic collection info
            result.append(f"## Collection: {collection_info.get('name', 'Unknown')}")
            result.append(f"Document count: {collection_info.get('count', 0)}")
            
            # Schema info
            if "schema" in collection_info:
                result.append("\n### Schema:")
                for field, field_info in collection_info["schema"].items():
                    types = ", ".join(field_info.get("types", ["unknown"]))
                    result.append(f"- {field}: {types}")
            
            # Sample document
            if include_sample and "sample_documents" in collection_info and collection_info["sample_documents"]:
                result.append("\n### Sample Document:")
                sample = collection_info["sample_documents"][0]
                sample_str = MongoDBResponseFormatter.format_document(sample, max_length=500)
                result.append(f"```json\n{sample_str}\n```")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error formatting MongoDB collection info: {str(e)}")
            return str(collection_info)
    
    @staticmethod
    def format_query_result(df, max_rows=10):
        """Format query result DataFrame as a readable string"""
        try:
            if df.empty:
                return "Query returned no results."
                
            total_rows = len(df)
            shown_rows = min(total_rows, max_rows)
            
            result = [f"Query returned {total_rows} documents.\n"]
            
            # Display the first max_rows rows
            result.append(df.head(max_rows).to_string())
            
            if total_rows > max_rows:
                result.append(f"\n... and {total_rows - max_rows} more documents")
                
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error formatting MongoDB query result: {str(e)}")
            return str(df)


# Function to patch an existing MongoDB agent system instance
def patch_agent_system(agent_system):
    """
    Patch an existing MongoDB agent system to add response capture functionality
    without requiring inheritance.
    
    Args:
        agent_system: The MongoDBAgentSystem instance to patch
        
    Returns:
        The patched agent system
    """
    try:
        logger.info("Patching MongoDB agent system for response capture")
        
        # Add response listeners attribute if it doesn't exist
        if not hasattr(agent_system, 'response_listeners'):
            agent_system.response_listeners = []
            logger.info("Added response_listeners attribute")
        
        # Add the add_response_listener method if it doesn't exist
        if not hasattr(agent_system, 'add_response_listener'):
            def add_response_listener(self, listener):
                self.response_listeners.append(listener)
                logger.info(f"Added response listener: {type(listener).__name__}")
            agent_system.add_response_listener = types.MethodType(add_response_listener, agent_system)
            logger.info("Added add_response_listener method")
        
        # Add the notify_listeners method if it doesn't exist
        if not hasattr(agent_system, 'notify_listeners'):
            def notify_listeners(self, agent_name, message, metadata=None):
                logger.info(f"Notifying listeners of response from {agent_name}")
                for listener in self.response_listeners:
                    if hasattr(listener, 'on_response'):
                        listener.on_response(agent_name, message, metadata)
                    elif callable(listener):
                        listener(agent_name, message, metadata)
            agent_system.notify_listeners = types.MethodType(notify_listeners, agent_system)
            logger.info("Added notify_listeners method")
        
        # Patch agent message handling if not already patched
        if not hasattr(agent_system, '_patched_messaging'):
            agent_system._patched_messaging = True
            logger.info("Patching agent messaging")
            
            # Patch MongoDB agents
            if hasattr(agent_system, 'agents'):
                for agent_name, agent in agent_system.agents.items():
                    logger.info(f"Patching agent: {agent_name}")
                    
                    # Patch the generate_reply method if it exists
                    if hasattr(agent, 'generate_reply'):
                        original_method = agent.generate_reply
                        
                        def create_patched_method(agent_name, orig_method):
                            def patched_method(self, *args, **kwargs):
                                # Call the original method with the original arguments
                                result = orig_method(*args, **kwargs)
                                
                                # Notify listeners with the result
                                if result:
                                    content = result.get("content", "") if isinstance(result, dict) else result
                                    agent_system.notify_listeners(agent_name, content)
                                
                                return result
                            return types.MethodType(patched_method, agent)
                        
                        agent.generate_reply = create_patched_method(agent_name, original_method)
                        logger.info(f"Patched generate_reply method for {agent_name}")
            
            # Patch the user proxy agent
            if hasattr(agent_system, 'user_proxy'):
                logger.info("Patching user proxy agent")
                
                # Patch the execute_function method to capture MongoDB-specific outputs
                if hasattr(agent_system.user_proxy, 'execute_function'):
                    original_method = agent_system.user_proxy.execute_function
                    
                    def patched_execute_function(self, function_name, **kwargs):
                        result = original_method(function_name, **kwargs)
                        
                        # Create appropriate metadata based on function name
                        metadata = None
                        
                        if function_name == 'execute_query' or function_name == 'execute_aggregation':
                            # Try to convert the result to a DataFrame if it's a string representing query results
                            try:
                                # Check if the result contains a data table
                                if "Query returned" in result or "Aggregation returned" in result:
                                    # This is just metadata for UI, not actually converting the data
                                    metadata = {"mongodb_type": "query_result"}
                            except:
                                pass
                        
                        elif function_name == 'explore_mongodb':
                            metadata = {"mongodb_type": "exploration"}
                            
                        elif function_name == 'get_exploration_notes':
                            metadata = {"mongodb_type": "exploration_notes"}
                            
                        elif function_name == 'create_visualization':
                            metadata = {"mongodb_type": "visualization"}
                            
                        # Notify listeners with the result and metadata
                        agent_system.notify_listeners("MongoDBUserProxy", result, metadata)
                        
                        return result
                    
                    agent_system.user_proxy.execute_function = types.MethodType(patched_execute_function, agent_system.user_proxy)
                    logger.info("Patched execute_function method for MongoDB user proxy")
        
        logger.info("Successfully patched MongoDB agent system")
        return agent_system
        
    except Exception as e:
        error_msg = f"Error patching MongoDB agent system: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        return agent_system