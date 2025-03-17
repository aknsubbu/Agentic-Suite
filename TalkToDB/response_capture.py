"""
This file contains classes to modify your existing DatabaseAgentSystem
to work with the Streamlit interface.

Add this code to your db_agnostic_agent.py file or create a new file
and import it into your main application.
"""

from typing import Dict, List, Any, Callable, Optional
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

class ResponseListener:
    """Interface for objects that listen to agent responses"""
    
    def on_response(self, agent_name: str, message: str, metadata: Optional[Dict] = None):
        """Handle a response from an agent"""
        pass

class ResponseCapture(ResponseListener):
    """Captures responses from agents for use with UI interfaces"""
    
    def __init__(self):
        self.responses = []
        self.latest_response = None
        
    def on_response(self, agent_name: str, message: str, metadata: Optional[Dict] = None):
        """Capture a response from an agent"""
        response = {
            "agent": agent_name,
            "content": message,
            "type": "text",
            "time": datetime.now().strftime("%H:%M:%S"),
            "metadata": metadata or {}
        }
        
        # Check if the response contains data (table/DataFrame)
        if metadata and "data" in metadata and isinstance(metadata["data"], pd.DataFrame):
            response["type"] = "data"
            response["data"] = metadata["data"]
            
        # Check if the response contains a visualization
        if metadata and "visualization" in metadata and isinstance(metadata["visualization"], go.Figure):
            response["type"] = "visualization"
            response["visualization"] = metadata["visualization"]
            
        self.responses.append(response)
        self.latest_response = response
        return response
    
    # Add an alias for compatibility with existing code
    capture_response = on_response

# Modify your DatabaseAgentSystem class to include this functionality
class DatabaseAgentSystemWithCapture:
    """
    This is a mixin class to add response capturing functionality to your
    existing DatabaseAgentSystem. To use it, modify your DatabaseAgentSystem
    to inherit from this class.
    
    Example:
    ```python
    class DatabaseAgentSystem(DatabaseAgentSystemWithCapture):
        # Your existing code...
        pass
    ```
    
    Or add these methods directly to your existing class.
    """
    
    def __init__(self, *args, **kwargs):
        # Initialize the response listeners list
        self.response_listeners = []
        
        # Call the parent class initialization
        super().__init__(*args, **kwargs)
        
        # Patch the agent's message handling
        self._patch_agent_messaging()
    
    def _patch_agent_messaging(self):
        """
        Patch the agents to capture their responses.
        This needs to be customized based on how your agent system works.
        """
        # Example: If your agents have a "send_message" method
        for agent_name, agent in self.agents.items():
            original_method = agent.send_message
            
            def patched_method(message, *args, **kwargs):
                result = original_method(message, *args, **kwargs)
                self.notify_listeners(agent_name, message)
                return result
                
            agent.send_message = patched_method
    
    def add_response_listener(self, listener: ResponseListener):
        """Add a response listener"""
        self.response_listeners.append(listener)
    
    def notify_listeners(self, agent_name: str, message: str, metadata: Optional[Dict] = None):
        """Notify all listeners of a new response"""
        for listener in self.response_listeners:
            listener.on_response(agent_name, message, metadata)
    
    def start_interaction(self, message: str):
        """
        Override the start_interaction method to capture responses.
        Make sure to call the original method!
        """
        # If you want to capture the final output for Streamlit:
        result = super().start_interaction(message)
        
        # If your interaction doesn't return anything but has side effects
        # (like printing to console), you'll need to modify your agent
        # interaction to capture these outputs.
        
        return result

# Add a standalone function to patch an existing agent system instance
def patch_agent_system(agent_system):
    """
    Patch an existing agent system to add response capture functionality
    without requiring inheritance.
    
    Args:
        agent_system: The DatabaseAgentSystem instance to patch
        
    Returns:
        The patched agent system
    """
    # Add response listeners attribute if it doesn't exist
    if not hasattr(agent_system, 'response_listeners'):
        agent_system.response_listeners = []
    
    # Add the add_response_listener method if it doesn't exist
    if not hasattr(agent_system, 'add_response_listener'):
        def add_response_listener(self, listener):
            self.response_listeners.append(listener)
        agent_system.add_response_listener = types.MethodType(add_response_listener, agent_system)
    
    # Add the notify_listeners method if it doesn't exist
    if not hasattr(agent_system, 'notify_listeners'):
        def notify_listeners(self, agent_name, message, metadata=None):
            for listener in self.response_listeners:
                if hasattr(listener, 'on_response'):
                    listener.on_response(agent_name, message, metadata)
                elif callable(listener):
                    listener(agent_name, message, metadata)
        agent_system.notify_listeners = types.MethodType(notify_listeners, agent_system)
    
    # Patch agent message handling if not already patched
    if not hasattr(agent_system, '_patched_messaging'):
        agent_system._patched_messaging = True
        
        # Custom patch logic based on your agent system's structure
        if hasattr(agent_system, 'agents'):
            for agent_name, agent in agent_system.agents.items():
                if hasattr(agent, 'send_message'):
                    original_method = agent.send_message
                    
                    def create_patched_method(agent_name, orig_method):
                        def patched_method(self, message, *args, **kwargs):
                            result = orig_method(message, *args, **kwargs)
                            agent_system.notify_listeners(agent_name, message)
                            return result
                        return types.MethodType(patched_method, agent)
                    
                    agent.send_message = create_patched_method(agent_name, original_method)
    
    return agent_system

# Don't forget to import types at the top of the file
import types

# Usage Example:
"""
# This shows how to use ResponseCapture with your agent system

from response_capture import ResponseCapture, patch_agent_system

# Method 1: Using inheritance (requires modifying class definition)
class DatabaseAgentSystem(DatabaseAgentSystemWithCapture):
    # Your existing code...
    pass

# Method 2: Using the patch function (works with existing instances)
# Create a response capture object
response_capture = ResponseCapture()

# Create your agent system
agent_system = DatabaseAgentSystem(
    db_explorer=your_db_explorer,
    openai_model=your_model,
    openai_key=your_key
)

# Patch the agent system to add response capture functionality
agent_system = patch_agent_system(agent_system)

# Add the response capture as a listener
agent_system.add_response_listener(response_capture)

# Now when you use start_interaction, responses will be captured
agent_system.start_interaction("Your message here")

# Access the captured responses
latest_response = response_capture.latest_response
all_responses = response_capture.responses
"""