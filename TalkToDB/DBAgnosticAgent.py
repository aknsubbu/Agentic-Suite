import os
import json
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

import autogen
from autogen import Agent, ConversableAgent, GroupChat, GroupChatManager
from autogen.agentchat.agent import Agent
from autogen import AssistantAgent
from autogen import UserProxyAgent

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dbInterface import DatabaseExplorer

class DatabaseUserProxy(UserProxyAgent):
    """User proxy agent with database capabilities for any database type"""
    
    def __init__(self, db_explorer: DatabaseExplorer, **kwargs):
        """Initialize with a database explorer and other UserProxyAgent parameters
        
        Args:
            db_explorer: An instance of a class implementing the DatabaseExplorer interface
            **kwargs: Additional parameters for UserProxyAgent
        """
        super().__init__(**kwargs)
        self.db_explorer = db_explorer
        self.exploration_notes = None
        
        # Register functions for database operations
        self.register_function(
            function_map={
                "explore_database": self.explore_database,
                "execute_query": self.execute_query,
                "execute_aggregation": self.execute_aggregation,
                "create_visualization": self.create_visualization,
                "get_exploration_notes": self.get_exploration_notes,
            }
        )
    
    def explore_database(self) -> str:
        """Explore the database and return notes"""
        try:
            exploration_results = self.db_explorer.explore_database()
            self.exploration_notes = self.db_explorer.generate_notes()
            
            # Get the number of collections/tables from the results
            collection_count = len(exploration_results.get("collections", {}))
            
            return f"Database exploration completed. Found {collection_count} collections/tables."
        except Exception as e:
            return f"Error exploring database: {str(e)}"
    
    def execute_query(self, collection_name: str, query: Any = None, 
                     limit: int = 100, sort = None) -> str:
        """Execute a database query and return results
        
        Args:
            collection_name: Name of the collection/table
            query: Query specification (format depends on database type)
            limit: Maximum number of results
            sort: Sort specification (format depends on database type)
            
        Returns:
            str: Formatted query results
        """
        try:
            # Convert string representation of query to dict/object if needed
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except json.JSONDecodeError:
                    return "Error: Invalid query JSON format"
            
            # Build query params
            query_params = {
                "query": query,
                "limit": limit,
                "sort": sort
            }
            
            # Execute the query
            df = self.db_explorer.execute_query(collection_name, query_params)
            
            # Return results
            if df.empty:
                return "Query returned no results."
            
            # Format the results
            results_str = f"Query returned {len(df)} records.\n"
            results_str += df.head(10).to_string()
            
            if len(df) > 10:
                results_str += f"\n... and {len(df) - 10} more rows"
                
            return results_str
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def execute_aggregation(self, collection_name: str, aggregation_params: Any) -> str:
        """Execute a database aggregation and return results
        
        Args:
            collection_name: Name of the collection/table
            aggregation_params: Aggregation specification (format depends on database type)
            
        Returns:
            str: Formatted aggregation results
        """
        try:
            # Convert string representation to appropriate format if needed
            if isinstance(aggregation_params, str):
                try:
                    aggregation_params = json.loads(aggregation_params)
                except json.JSONDecodeError:
                    return "Error: Invalid aggregation parameters JSON format"
            
            # Execute the aggregation
            df = self.db_explorer.execute_aggregation(collection_name, aggregation_params)
            
            # Return results
            if df.empty:
                return "Aggregation returned no results."
            
            # Format the results
            results_str = f"Aggregation returned {len(df)} records.\n"
            results_str += df.head(10).to_string()
            
            if len(df) > 10:
                results_str += f"\n... and {len(df) - 10} more rows"
                
            return results_str
        except Exception as e:
            return f"Error executing aggregation: {str(e)}"
    
    def create_visualization(self, collection_name: str, viz_type: str, 
                           query: Any = None, params: Dict = None, 
                           output_path: str = None) -> str:
        """Create a visualization from database data
        
        Args:
            collection_name: Name of the collection/table
            viz_type: Type of visualization (bar, line, scatter, pie, histogram)
            query: Query to filter data (format depends on database type)
            params: Visualization parameters
            output_path: Path to save the visualization
            
        Returns:
            str: Result message
        """
        if query is None:
            query = {}
            
        if params is None:
            params = {}
            
        # Convert string representations if needed
        if isinstance(query, str):
            try:
                query = json.loads(query)
            except json.JSONDecodeError:
                return "Error: Invalid query JSON format"
                
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                return "Error: Invalid params JSON format"
        
        try:
            # Get the data
            query_params = {"query": query, "limit": params.get("limit", 1000)}
            df = self.db_explorer.execute_query(collection_name, query_params)
            
            if df.empty:
                return "Query returned no data to visualize."
            
            # Check required parameters for the visualization
            required_params = {
                "bar": ["x", "y"],
                "line": ["x", "y"],
                "scatter": ["x", "y"],
                "pie": ["names", "values"],
                "histogram": ["x"],
            }
            
            if viz_type not in required_params:
                return f"Unsupported visualization type: {viz_type}"
            
            for param in required_params[viz_type]:
                if param not in params:
                    return f"Missing required parameter '{param}' for {viz_type} visualization"
            
            # Create the figure
            fig = None
            
            if viz_type == "bar":
                fig = px.bar(df, x=params["x"], y=params["y"], 
                           title=params.get("title", f"Bar Chart of {params['y']} by {params['x']}"))
                
            elif viz_type == "line":
                fig = px.line(df, x=params["x"], y=params["y"], 
                            title=params.get("title", f"Line Chart of {params['y']} over {params['x']}"))
                
            elif viz_type == "scatter":
                fig = px.scatter(df, x=params["x"], y=params["y"], 
                               color=params.get("color"), size=params.get("size"),
                               title=params.get("title", f"Scatter Plot of {params['y']} vs {params['x']}"))
                
            elif viz_type == "pie":
                fig = px.pie(df, names=params["names"], values=params["values"], 
                           title=params.get("title", f"Pie Chart of {params['values']} by {params['names']}"))
                
            elif viz_type == "histogram":
                fig = px.histogram(df, x=params["x"], 
                                 title=params.get("title", f"Histogram of {params['x']}"))
            
            # Save the figure if output path is provided
            if output_path:
                fig.write_html(output_path)
                return f"Visualization saved to {output_path}"
            else:
                # Generate a default filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"visualization_{viz_type}_{timestamp}.html"
                fig.write_html(filename)
                return f"Visualization saved to {filename}"
                
        except Exception as e:
            return f"Error creating visualization: {str(e)}"
    
    def get_exploration_notes(self) -> str:
        """Get the exploration notes"""
        if not self.exploration_notes:
            return "Database has not been explored yet. Call explore_database() first."
            
        return self.exploration_notes



class DatabaseAgentSystem():
    """A multi-agent system for database analysis that works with any database type"""
    
    def __init__(self, db_explorer: DatabaseExplorer, openai_model:str, openai_key:str):
        """Initialize the multi-agent system with a database explorer
        
        Args:
            db_explorer: An instance of a class implementing the DatabaseExplorer interface
        """
        self.db_explorer = db_explorer
        self.user_proxy = None
        self.agents = {}
        self.openai_model = openai_model
        self.openai_key = openai_key
        
        # Set up the agents
        self._setup_agents()
        
    def _setup_agents(self):
        """Set up the specialized agents for the system"""
        
        # Create the user proxy with database capabilities
        self.user_proxy = DatabaseUserProxy(
            db_explorer=self.db_explorer,
            name="UserProxy",
            human_input_mode="TERMINATE",
            code_execution_config={"use_docker": False}
        )
        
        # Create a database explorer agent
        self.agents["db_explorer"] = AssistantAgent(
            name="DatabaseExplorer",
            llm_config={
                "temperature": 0.1,
                "model": self.openai_model,
                "api_key": self.openai_key
            },
            system_message="""You are a MongoDB database exploration specialist.
Your role is to understand MongoDB database structure, schema, and relationships.
You analyze collections, document structures, and identify patterns in MongoDB databases.

IMPORTANT: You must use the provided Python functions to interact with the database, NOT MongoDB shell commands.

Your primary responsibilities:
1. Exploring MongoDB collections and their document schemas 
2. Identifying relationships between collections using field references
3. Explaining MongoDB database structure in clear, concise terms
4. Providing insights about MongoDB data organization

When asked about the MongoDB database:
1. FIRST call explore_database() function to discover the database structure
2. Then use get_exploration_notes() function to access detailed information
3. Use these Python functions, NOT MongoDB shell commands like db.collection.find()

Example of how to use the provided functions:
```python
# First explore the database
explore_database()

# Then get the exploration notes
exploration_notes = get_exploration_notes()
print(exploration_notes)
```

Always explain the MongoDB database structure in user-friendly terms.
"""
        )
        
        # Create a query specialist agent
        self.agents["query_specialist"] = AssistantAgent(
            name="QuerySpecialist",
            llm_config={
                "temperature": 0.2,
                "model": self.openai_model,
                "api_key": self.openai_key
            },
            system_message="""You are a MongoDB query specialist.
Your expertise is in writing efficient, correct MongoDB queries.
You translate user questions into precise MongoDB operations using the provided Python functions.

IMPORTANT: You must use the provided Python functions to interact with the database, NOT MongoDB shell commands.

Your primary responsibilities:
1. Writing MongoDB queries to retrieve specific data
2. Creating MongoDB aggregation pipelines for data analysis
3. Optimizing MongoDB queries for performance
4. Explaining MongoDB query structure and logic

For simple queries, use the execute_query() function with these parameters:
- collection_name: The name of the MongoDB collection
- query: A MongoDB query in JSON or dictionary format (e.g., {"field": "value"})
- limit: Maximum number of results to return
- sort: Sort specification

Example of how to use execute_query():
```python
# Count documents in a collection
result = execute_query("users", {})
print(f"Users collection has {len(result)} documents")

# Query with filters
active_users = execute_query("users", {"active": True}, limit=10)
print(f"Found {len(active_users)} active users")
```

For aggregations, use the execute_aggregation() function with these parameters:
- collection_name: The name of the MongoDB collection
- aggregation_params: A MongoDB aggregation pipeline as a list of dictionaries

Example of how to use execute_aggregation():
```python
# Find users with most activities
top_users = execute_aggregation(
    "activities",
    [
        {"$group": {"_id": "$userId", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
)
print(f"Top users by activity: {top_users}")
```

Always use the provided Python functions, NOT MongoDB shell commands.
"""
        )
        
        # Create a data visualization agent
        self.agents["viz_specialist"] = AssistantAgent(
            name="VisualizationSpecialist",
            llm_config={
                "temperature": 0.3,
                "model": self.openai_model,
                "api_key": self.openai_key
            },
            system_message="""You are a data visualization specialist working with MongoDB data.
Your expertise is in creating effective visualizations to communicate insights from MongoDB collections.
You select appropriate chart types based on document structures and analysis goals.

IMPORTANT: You must use the provided Python functions to interact with the database, NOT MongoDB shell commands.

Your primary responsibilities:
1. Selecting appropriate visualization types for MongoDB data
2. Configuring visualization parameters for clarity
3. Creating visually appealing and informative charts
4. Explaining visualization choices and insights

To create visualizations, follow this workflow:
1. Get data using execute_query() or execute_aggregation() functions
2. Create visualizations using the create_visualization() function

Example workflow:
```python
# First get the data
activity_types = execute_aggregation(
    "activities",
    [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
)

# Then visualize it
create_visualization(
    "activities",
    "bar",
    params={
        "x": "_id",
        "y": "count",
        "title": "Activity Counts by Type"
    }
)
```

Always use the provided Python functions, NOT MongoDB shell commands.
"""
        )
        
        # Create the group chat manager
        self.group_chat = GroupChat(
            agents=[
                self.user_proxy,
                self.agents["db_explorer"],
                self.agents["query_specialist"],
                self.agents["viz_specialist"]
            ],
            messages=[],
            max_round=12
        )
        
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config={
                "temperature": 0.2,
                "model": self.openai_model,
                "api_key": self.openai_key
            }
        )
    
    def start_interaction(self, message: str = None):
        """Start the interaction with the multi-agent system"""
        if message is None:
            message = """I need help with analyzing my database. 
Please first explore the database to understand its structure, 
then help me answer questions and visualize the data."""
        
        # Start the chat
        self.user_proxy.initiate_chat(
            self.manager,
            message=message
        )

# Example of how to use the system with a MongoDB explorer
if __name__ == "__main__":
    # Import MongoDB explorer implementation
    from DB_Interfaces.mongoDBExplorer import MongoDBExplorer
    
    # Create a MongoDB explorer
    mongodb_explorer = MongoDBExplorer(db_name="target",connection_string='mongodb+srv://aknsubbu:sfvlfg51Bun6JhAq@cluster0.xljk6.mongodb.net/')
    
    # Initialize the multi-agent system with the MongoDB explorer
    agent_system = DatabaseAgentSystem(db_explorer=mongodb_explorer,openai_model='gpt-4o-mini',openai_key='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')
    
    # Start interaction with specific request
    agent_system.start_interaction(
        message="""
First, explore the database to understand its structure.
Then, perform the following tasks:
1. Show me how many records are in each table/collection
2. Find the users who have the most activity
3. Create a bar chart showing the distribution of data
4. Identify any interesting patterns or insights
"""
    )