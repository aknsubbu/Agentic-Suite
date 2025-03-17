import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import base64
from io import BytesIO
import re
import uuid
from typing import Dict, List, Any, Optional
import traceback

import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import your actual database system components
from dbInterface import DatabaseExplorer
from DB_Interfaces.mongoDBExplorer import MongoDBExplorer
from DB_Interfaces.SQLDBExplorer import SQLDatabaseExplorer
from DBAgnosticAgent import DatabaseAgentSystem

# Utility function to create a database explorer with simplified connection
def get_database_explorer(db_type: str, connection_string: str, db_name: str = None) -> DatabaseExplorer:
    """Create the appropriate database explorer based on type and connection string"""
    try:
        if db_type == "MongoDB":
            # Create MongoDB explorer with connection string and db_name
            if not db_name:
                # Try to extract db_name from connection string if not provided separately
                # MongoDB connection strings typically follow this pattern: mongodb://user:password@host:port/database
                try:
                    from urllib.parse import urlparse
                    parsed_uri = urlparse(connection_string)
                    auto_db_name = parsed_uri.path.strip('/')
                    if auto_db_name:
                        db_name = auto_db_name
                    else:
                        raise ValueError("Database name is required but could not be extracted from connection string")
                except Exception as e:
                    raise ValueError(f"Database name is required: {str(e)}")
                    
            return MongoDBExplorer(db_name=db_name, connection_string=connection_string)
            
        elif db_type == "SQL (MySQL/PostgreSQL)" or db_type == "SQLite":
            # Create SQL explorer directly from connection string
            return SQLDatabaseExplorer(connection_string=connection_string)
            
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
            
    except Exception as e:
        st.error(f"Failed to create database explorer: {str(e)}")
        traceback.print_exc()
        raise e


# Custom Response Capture Class
class ResponseCapture:
    """Captures responses from the agent system's conversation"""
    
    def __init__(self):
        self.responses = []
        self.latest_response = None
        
    def capture_response(self, sender, message, metadata=None):
        """Capture a response from an agent in the conversation"""
        response = {
            "agent": sender,
            "content": message,
            "type": "text",
            "time": datetime.now().strftime("%H:%M:%S"),
            "metadata": metadata or {}
        }
        
        # Check if the message contains data (table/DataFrame)
        if metadata and "data" in metadata:
            response["type"] = "data"
            response["data"] = metadata["data"]
            
        # Check if the message contains a visualization
        if metadata and "visualization" in metadata:
            response["type"] = "visualization"
            response["visualization"] = metadata["visualization"]
            
        self.responses.append(response)
        self.latest_response = response
        return response

# Create a custom wrapper for the DatabaseAgentSystem
class StreamlitDatabaseAgent:
    """A wrapper around DatabaseAgentSystem that captures responses for Streamlit UI"""
    
    def __init__(self, db_explorer: DatabaseExplorer, openai_model: str, openai_key: str):
        """Initialize with database explorer and OpenAI credentials"""
        self.agent_system = DatabaseAgentSystem(
            db_explorer=db_explorer,
            openai_model=openai_model,
            openai_key=openai_key
        )
        self.response_capture = ResponseCapture()
        self.register_response_listeners()
        
    def register_response_listeners(self):
        """Register listeners for agent responses"""
        # This requires modifying your DatabaseAgentSystem class to support response listeners
        # Example of what to add to your existing class:
        # 
        # def add_response_listener(self, listener_function):
        #     self.response_listeners.append(listener_function)
        #
        # def notify_listeners(self, sender, message, metadata=None):
        #     for listener in self.response_listeners:
        #         listener(sender, message, metadata)
        
        # If your system already supports some form of response capturing,
        # connect it to the response_capture.capture_response method
        
        # For now, we'll assume you've added this functionality
        self.agent_system.add_response_listener(self.response_capture.capture_response)
        
    def get_response(self, message: str) -> Dict:
        """Process a message and return the response"""
        try:
            # Clear the previous latest response
            self.response_capture.latest_response = None
            
            # Start the interaction
            self.agent_system.start_interaction(message)
            
            # Return the captured response
            if self.response_capture.latest_response:
                return self.response_capture.latest_response
            else:
                # If no response was captured, create a default one
                return {
                    "agent": "System",
                    "content": "I processed your request but didn't generate a specific response.",
                    "type": "text",
                    "time": datetime.now().strftime("%H:%M:%S")
                }
                
        except Exception as e:
            # Log the full error for debugging
            st.error(f"Error processing message: {str(e)}")
            traceback.print_exc()
            
            # Return an error response
            return {
                "agent": "System",
                "content": f"Error processing message: {str(e)}",
                "type": "text",
                "time": datetime.now().strftime("%H:%M:%S")
            }

# Function to create and configure the agent system
def create_agent_system(db_explorer: DatabaseExplorer, openai_model: str, openai_key: str) -> StreamlitDatabaseAgent:
    """Create and configure the agent system with the database explorer"""
    try:
        # Create the custom agent wrapper
        return StreamlitDatabaseAgent(
            db_explorer=db_explorer,
            openai_model=openai_model,
            openai_key=openai_key
        )
    except Exception as e:
        st.error(f"Failed to create agent system: {str(e)}")
        raise e

# Main application function
def main():
    # Set page configuration
    st.set_page_config(
        page_title="Database AI Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'db_connected' not in st.session_state:
        st.session_state.db_connected = False
    if 'db_explorer' not in st.session_state:
        st.session_state.db_explorer = None
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if 'api_key_valid' not in st.session_state:
        st.session_state.api_key_valid = False
    
    # Main header
    st.markdown('<h1 class="main-header">🤖 Database AI Agent</h1>', unsafe_allow_html=True)
    st.markdown('An intelligent multi-agent system for database exploration, analysis, and visualization.')
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Connection", "Chat Interface", "History"])
    
    with tab1:
        # Database connection tab
        render_connection_tab()
        
    with tab2:
        # Chat interface tab
        render_chat_tab()
        
    with tab3:
        # History tab
        render_history_tab()
    
    # Footer
    render_footer()

# def render_connection_tab():
#     """Render the database connection tab with simplified connection string input"""
#     st.markdown('<h2 class="sub-header">Database Connection</h2>', unsafe_allow_html=True)
    
#     # Database configuration form
#     with st.form(key='database_form', clear_on_submit=False):
#         st.markdown('<div class="database-form">', unsafe_allow_html=True)
        
#         # Database Type selection
#         db_type = st.selectbox(
#             "Database Type",
#             ["MongoDB", "SQL (MySQL/PostgreSQL)", "SQLite"],
#             help="Select your database type"
#         )
        
#         # Connection string input with appropriate examples based on database type
#         if db_type == "MongoDB":
#             connection_example = "mongodb://username:password@localhost:27017/database_name"
#             connection_help = "Example: mongodb://localhost:27017/mydatabase or mongodb://username:password@host:port/database"
#         elif db_type == "SQL (MySQL/PostgreSQL)":
#             connection_example = "mysql+pymysql://username:password@localhost:3306/database_name"
#             connection_help = "MySQL: mysql+pymysql://username:password@host:port/database\nPostgreSQL: postgresql://username:password@host:port/database"
#         elif db_type == "SQLite":
#             connection_example = "sqlite:///path/to/database.db"
#             connection_help = "Example: sqlite:///mydatabase.db or sqlite:////absolute/path/to/database.db"
        
#         # Connection string input
#         connection_string = st.text_input(
#             "Connection String", 
#             placeholder=connection_example,
#             help=connection_help
#         )
        
#         # Add info about connection strings
#         with st.expander("Connection String Help"):
#             if db_type == "MongoDB":
#                 st.markdown("""
#                 **MongoDB Connection String Format:**
#                 ```
#                 mongodb://[username:password@]host[:port]/database[?options]
#                 ```
                
#                 **Examples:**
#                 - Simple connection: `mongodb://localhost:27017/mydatabase`
#                 - With authentication: `mongodb://myusername:mypassword@localhost:27017/mydatabase`
#                 - Multiple hosts (replica set): `mongodb://host1:27017,host2:27017/mydatabase?replicaSet=myrs`
#                 """)
#             elif db_type == "SQL (MySQL/PostgreSQL)":
#                 st.markdown("""
#                 **MySQL Connection String Format:**
#                 ```
#                 mysql+pymysql://username:password@host:port/database
#                 ```
                
#                 **PostgreSQL Connection String Format:**
#                 ```
#                 postgresql://username:password@host:port/database
#                 ```
                
#                 **Examples:**
#                 - MySQL: `mysql+pymysql://root:mypassword@localhost:3306/mydatabase`
#                 - PostgreSQL: `postgresql://postgres:mypassword@localhost:5432/mydatabase`
#                 """)
#             elif db_type == "SQLite":
#                 st.markdown("""
#                 **SQLite Connection String Format:**
#                 ```
#                 sqlite:///path/to/database.db
#                 ```
                
#                 **Examples:**
#                 - Relative path: `sqlite:///mydatabase.db`
#                 - Absolute path: `sqlite:////absolute/path/to/mydatabase.db`
#                 - In-memory database: `sqlite:///:memory:`
#                 """)
        
#         # OpenAI Configuration
#         st.markdown("#### OpenAI Configuration")
#         col1, col2 = st.columns(2)
#         with col1:
#             openai_model = st.selectbox(
#                 "OpenAI Model",
#                 ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo","gpt-4o-mini"],
#                 help="Select the OpenAI model to use"
#             )
#         with col2:
#             openai_key = st.text_input("OpenAI API Key", type="password", help="Your OpenAI API key")
#             # Option to load from environment variable
#             use_env_var = st.checkbox("Use OPENAI_API_KEY environment variable", 
#                                      help="Load API key from environment variable")
#             if use_env_var:
#                 openai_key = os.environ.get("OPENAI_API_KEY", "")
        
#         st.markdown('</div>', unsafe_allow_html=True)
        
#         # Submit button
#         submit_button = st.form_submit_button(label="Connect to Database")
        
#         if submit_button:
#             # Validate inputs
#             if not connection_string:
#                 st.error("Connection string is required")
#             elif not openai_key:
#                 st.error("OpenAI API Key is required")
#             else:
#                 with st.spinner("Connecting to database..."):
#                     try:
#                         # Create database explorer with connection string
#                         db_explorer = get_database_explorer(db_type, connection_string)
#                         st.session_state.db_explorer = db_explorer
                        
#                         # Create agent system
#                         agent_system = create_agent_system(db_explorer, openai_model, openai_key)
#                         st.session_state.agent = agent_system
                        
#                         # Set connected flag
#                         st.session_state.db_connected = True
#                         st.session_state.api_key_valid = True
                        
#                         st.success(f"Successfully connected to {db_type} database!")
                        
#                         # Add initial system message
#                         st.session_state.messages.append({
#                             "role": "system",
#                             "content": f"Connected to {db_type} database. I'm ready to help you explore and analyze your data!",
#                             "type": "text",
#                             "time": datetime.now().strftime("%H:%M:%S")
#                         })
                        
#                     except Exception as e:
#                         st.error(f"Failed to connect to database: {str(e)}")
#                         traceback.print_exc()
    
#     # Connection status indicator
#     st.markdown("### Connection Status")
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.session_state.db_connected:
#             st.success("✅ Connected to Database")
#         else:
#             st.error("❌ Not Connected")
#     with col2:
#         if st.session_state.api_key_valid:
#             st.success("✅ OpenAI API Key Valid")
#         else:
#             st.error("❌ OpenAI API Key Not Verified")

def render_connection_tab():
    """Render the database connection tab with simplified connection string input"""
    st.markdown('<h2 class="sub-header">Database Connection</h2>', unsafe_allow_html=True)
    
    # Database configuration form
    with st.form(key='database_form', clear_on_submit=False):
        st.markdown('<div class="database-form">', unsafe_allow_html=True)
        
        # Database Type selection
        db_type = st.selectbox(
            "Database Type",
            ["MongoDB", "SQL (MySQL/PostgreSQL)", "SQLite"],
            help="Select your database type"
        )
        
        # Connection string input with appropriate examples based on database type
        if db_type == "MongoDB":
            connection_example = "mongodb://username:password@localhost:27017/database_name"
            connection_help = "Example: mongodb://localhost:27017/mydatabase or mongodb://username:password@host:port/database"
            # Add database name input field for MongoDB
            db_name = st.text_input(
                "Database Name (leave blank to extract from connection string)",
                help="The name of the MongoDB database to connect to"
            )
        elif db_type == "SQL (MySQL/PostgreSQL)":
            connection_example = "mysql+pymysql://username:password@localhost:3306/database_name"
            connection_help = "MySQL: mysql+pymysql://username:password@host:port/database\nPostgreSQL: postgresql://username:password@host:port/database"
            db_name = None  # Not needed for SQL as it's in the connection string
        elif db_type == "SQLite":
            connection_example = "sqlite:///path/to/database.db"
            connection_help = "Example: sqlite:///mydatabase.db or sqlite:////absolute/path/to/database.db"
            db_name = None  # Not needed for SQLite
        
        # Connection string input
        connection_string = st.text_input(
            "Connection String", 
            placeholder=connection_example,
            help=connection_help
        )
        
        # OpenAI Configuration
        st.markdown("#### OpenAI Configuration")
        col1, col2 = st.columns(2)
        with col1:
            openai_model = st.selectbox(
                "OpenAI Model",
                ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo","gpt-4o-mini"],
                help="Select the OpenAI model to use"
            )
        with col2:
            openai_key = st.text_input("OpenAI API Key", type="password", help="Your OpenAI API key")
            # Option to load from environment variable
            use_env_var = st.checkbox("Use OPENAI_API_KEY environment variable", 
                                     help="Load API key from environment variable")
            if use_env_var:
                openai_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Submit button
        submit_button = st.form_submit_button(label="Connect to Database")
        
        if submit_button:
            # Validate inputs
            if not connection_string:
                st.error("Connection string is required")
            elif db_type == "MongoDB" and not (db_name or "/" in connection_string):
                st.error("For MongoDB, either provide a database name or include it in the connection string")
            elif not openai_key:
                st.error("OpenAI API Key is required")
            else:
                with st.spinner("Connecting to database..."):
                    try:
                        # Create database explorer with connection string and db_name
                        db_explorer = get_database_explorer(db_type, connection_string, db_name if db_type == "MongoDB" else None)
                        st.session_state.db_explorer = db_explorer
                        
                        # Create agent system
                        agent_system = create_agent_system(db_explorer, openai_model, openai_key)
                        st.session_state.agent = agent_system
                        
                        # Set connected flag
                        st.session_state.db_connected = True
                        st.session_state.api_key_valid = True
                        
                        st.success(f"Successfully connected to {db_type} database!")
                        
                        # Add initial system message
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"Connected to {db_type} database. I'm ready to help you explore and analyze your data!",
                            "type": "text",
                            "time": datetime.now().strftime("%H:%M:%S")
                        })
                        
                    except Exception as e:
                        st.error(f"Failed to connect to database: {str(e)}")
                        traceback.print_exc()



def render_chat_tab():
    """Render the chat interface tab"""
    st.markdown('<h2 class="sub-header">Chat Interface</h2>', unsafe_allow_html=True)
    
    # Chat interface
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="message-container user-message">'
                          f'<strong>You ({message["time"]}):</strong><br/>{message["content"]}'
                          f'</div>', unsafe_allow_html=True)
            else:  # system or assistant
                # Determine the agent tag
                agent_class = ""
                agent_name = message.get("agent", "System")
                
                if agent_name == "DatabaseExplorer":
                    agent_class = "agent-explorer"
                    agent_display = "Explorer"
                elif agent_name == "QuerySpecialist":
                    agent_class = "agent-query"
                    agent_display = "Query Specialist"
                elif agent_name == "VisualizationSpecialist":
                    agent_class = "agent-viz"
                    agent_display = "Viz Specialist"
                elif agent_name == "GroupChatManager":
                    agent_class = "agent-manager"
                    agent_display = "Manager"
                else:
                    agent_class = "agent-manager"
                    agent_display = "System"
                
                # Start the message container
                st.markdown(f'<div class="message-container assistant-message">'
                          f'<span class="agent-tag {agent_class}">{agent_display}</span>'
                          f'<strong>Assistant ({message["time"]}):</strong><br/>{message["content"]}'
                          f'</div>', unsafe_allow_html=True)
                
                # If the message contains data, display it
                if message.get("type") == "data" and "data" in message:
                    with st.expander("View Data", expanded=True):
                        st.dataframe(message["data"])
                        
                        # Add export buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            csv = message["data"].to_csv(index=False)
                            b64 = base64.b64encode(csv.encode()).decode()
                            href = f'<a href="data:file/csv;base64,{b64}" download="data_export.csv">Download CSV</a>'
                            st.markdown(href, unsafe_allow_html=True)
                        with col2:
                            excel_buffer = BytesIO()
                            message["data"].to_excel(excel_buffer, index=False)
                            excel_buffer.seek(0)
                            b64 = base64.b64encode(excel_buffer.getvalue()).decode()
                            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="data_export.xlsx">Download Excel</a>'
                            st.markdown(href, unsafe_allow_html=True)
                        with col3:
                            json_str = message["data"].to_json(orient="records")
                            b64 = base64.b64encode(json_str.encode()).decode()
                            href = f'<a href="data:file/json;base64,{b64}" download="data_export.json">Download JSON</a>'
                            st.markdown(href, unsafe_allow_html=True)
                
                # If the message contains a visualization, display it
                if message.get("type") == "visualization" and "visualization" in message:
                    with st.expander("View Visualization", expanded=True):
                        st.plotly_chart(message["visualization"], use_container_width=True)
                        
                        # Add download button for the visualization
                        buf = BytesIO()
                        message["visualization"].write_image(buf, format="png")
                        buf.seek(0)
                        b64 = base64.b64encode(buf.getvalue()).decode()
                        href = f'<a href="data:image/png;base64,{b64}" download="visualization.png">Download Visualization as PNG</a>'
                        st.markdown(href, unsafe_allow_html=True)
    
    # Chat input
    if st.session_state.db_connected:
        # Message input
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        
        with st.form(key='message_form', clear_on_submit=True):
            user_input = st.text_area("Type your message:", height=100, 
                                     help="Ask questions about your database or request analyses")
            col1, col2 = st.columns([1, 5])
            with col1:
                submit_message = st.form_submit_button("Send")
                
        if submit_message and user_input:
            # Add user message to chat
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "type": "text",
                "time": datetime.now().strftime("%H:%M:%S")
            })
            
            # Process with agent and get response
            with st.spinner("Thinking..."):
                try:
                    # Get response from agent system
                    response = st.session_state.agent.get_response(user_input)
                    
                    # Add agent response to chat
                    st.session_state.messages.append(response)
                    
                    # Rerun to update the UI with the new messages
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"Error processing message: {str(e)}")
                    traceback.print_exc()
                    
                    # Add error message to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "agent": "System",
                        "content": f"Error: {str(e)}",
                        "type": "text",
                        "time": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Rerun to update the UI
                    st.experimental_rerun()
                
        # Suggested queries to help users get started
        if len(st.session_state.messages) <= 1:  # Only show suggestions at the beginning
            st.markdown("### Suggested Queries")
            suggestion_cols = st.columns(3)
            
            suggestions = [
                "Explore the database structure",
                "Find the most active users",
                "Create a visualization of data distribution"
            ]
            
            for i, suggestion in enumerate(suggestions):
                with suggestion_cols[i]:
                    if st.button(suggestion):
                        # Add the suggestion as a user message
                        st.session_state.messages.append({
                            "role": "user",
                            "content": suggestion,
                            "type": "text",
                            "time": datetime.now().strftime("%H:%M:%S")
                        })
                        
                        # Process with agent and get response
                        with st.spinner("Thinking..."):
                            try:
                                # Get response from agent system
                                response = st.session_state.agent.get_response(suggestion)
                                
                                # Add agent response to chat
                                st.session_state.messages.append(response)
                                
                                # Rerun to update the UI
                                st.experimental_rerun()
                                
                            except Exception as e:
                                st.error(f"Error processing message: {str(e)}")
                                
                                # Add error message to chat
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "agent": "System",
                                    "content": f"Error: {str(e)}",
                                    "type": "text",
                                    "time": datetime.now().strftime("%H:%M:%S")
                                })
                                
                                # Rerun to update the UI
                                st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please connect to a database first in the Connection tab.")

def render_history_tab():
    """Render the conversation history tab"""
    st.markdown('<h2 class="sub-header">Conversation History</h2>', unsafe_allow_html=True)
    
    # Conversation management
    if len(st.session_state.messages) > 0:
        # Allow saving the conversation
        st.markdown("### Save Current Conversation")
        save_name = st.text_input("Conversation Name", f"Conversation-{st.session_state.conversation_id[:8]}")
        
        if st.button("Save Conversation"):
            # Create a directory for saved conversations if it doesn't exist
            os.makedirs("saved_conversations", exist_ok=True)
            
            # Prepare the conversation data
            conversation_data = {
                "id": st.session_state.conversation_id,
                "name": save_name,
                "timestamp": datetime.now().isoformat(),
                "messages": []
            }
            
            # Copy messages without visualization objects and dataframes
            for msg in st.session_state.messages:
                # Create a simplified copy of the message
                msg_copy = {
                    "role": msg["role"],
                    "content": msg["content"],
                    "time": msg["time"],
                    "type": msg["type"]
                }
                
                # Add agent name if present
                if "agent" in msg:
                    msg_copy["agent"] = msg["agent"]
                    
                # Add to conversation data
                conversation_data["messages"].append(msg_copy)
            
            # Save to file
            filename = f"saved_conversations/{save_name}_{st.session_state.conversation_id}.json"
            with open(filename, "w") as f:
                json.dump(conversation_data, f, indent=2)
                
            st.success(f"Conversation '{save_name}' saved successfully to {filename}!")
        
        # Allow clearing the conversation
        if st.button("Clear Current Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_id = str(uuid.uuid4())
            st.experimental_rerun()
        
        # Option to export conversation
        st.markdown("### Export Conversation")
        export_format = st.selectbox("Export Format", ["JSON", "Text", "HTML"])
        
        if st.button("Export"):
            with st.spinner("Preparing export..."):
                if export_format == "JSON":
                    # Convert to JSON
                    export_data = []
                    for msg in st.session_state.messages:
                        # Create a copy without any visualizations or dataframes
                        msg_copy = {k: v for k, v in msg.items() 
                                  if k not in ["visualization", "data"]}
                        export_data.append(msg_copy)
                        
                    json_str = json.dumps(export_data, indent=2)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    href = f'<a href="data:file/json;base64,{b64}" download="conversation_export.json">Download JSON</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                elif export_format == "Text":
                    # Convert to text
                    text_lines = []
                    for msg in st.session_state.messages:
                        sender = "You" if msg["role"] == "user" else "Assistant"
                        text_lines.append(f"{sender} ({msg['time']}): {msg['content']}")
                        
                    text_content = "\n\n".join(text_lines)
                    b64 = base64.b64encode(text_content.encode()).decode()
                    href = f'<a href="data:text/plain;base64,{b64}" download="conversation_export.txt">Download Text</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                elif export_format == "HTML":
                    # Convert to HTML
                    html_lines = ["<html><head><title>Conversation Export</title>",
                                 "<style>body{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;}",
                                 ".msg{padding:10px;margin:10px 0;border-radius:5px;}",
                                 ".user{background-color:#f0f0f0;}",
                                 ".assistant{background-color:#f8f8f8;}</style></head><body>",
                                 "<h1>Conversation Export</h1>"]
                    
                    for msg in st.session_state.messages:
                        css_class = "user" if msg["role"] == "user" else "assistant"
                        sender = "You" if msg["role"] == "user" else "Assistant"
                        agent = f" ({msg.get('agent', 'System')})" if msg["role"] == "assistant" else ""
                        
                        html_lines.append(f'<div class="msg {css_class}">')
                        html_lines.append(f'<strong>{sender}{agent} ({msg["time"]}):</strong><br/>')
                        html_lines.append(f'{msg["content"]}')
                        html_lines.append('</div>')
                        
                    html_lines.append("</body></html>")
                    html_content = "\n".join(html_lines)
                    b64 = base64.b64encode(html_content.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="conversation_export.html">Download HTML</a>'
                    st.markdown(href, unsafe_allow_html=True)
        
        # Show saved conversations
        st.markdown("### Saved Conversations")
        if os.path.exists("saved_conversations"):
            saved_files = [f for f in os.listdir("saved_conversations") if f.endswith(".json")]
            
            if saved_files:
                saved_conversations = []
                
                for file in saved_files:
                    try:
                        with open(f"saved_conversations/{file}", "r") as f:
                            data = json.load(f)
                            saved_conversations.append({
                                "filename": file,
                                "name": data.get("name", file),
                                "timestamp": data.get("timestamp", "Unknown"),
                                "message_count": len(data.get("messages", []))
                            })
                    except Exception as e:
                        st.warning(f"Could not read file {file}: {str(e)}")
                
                # Sort by timestamp (newest first)
                saved_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
                
                # Display as a table
                saved_df = pd.DataFrame(saved_conversations)
                saved_df = saved_df.rename(columns={
                    "name": "Conversation Name",
                    "timestamp": "Saved On",
                    "message_count": "Messages"
                })
                
                st.dataframe(saved_df[["Conversation Name", "Saved On", "Messages"]])
                
                # Allow loading a conversation
                selected_conversation = st.selectbox(
                    "Select a conversation to load:",
                    options=[conv["filename"] for conv in saved_conversations],
                    format_func=lambda x: next((c["name"] for c in saved_conversations if c["filename"] == x), x)
                )
                
                if st.button("Load Selected Conversation"):
                    try:
                        with open(f"saved_conversations/{selected_conversation}", "r") as f:
                            data = json.load(f)
                            
                            # Replace current conversation
                            st.session_state.messages = data.get("messages", [])
                            st.session_state.conversation_id = data.get("id", str(uuid.uuid4()))
                            
                            st.success(f"Loaded conversation '{data.get('name')}'")
                            st.experimental_rerun()
                            
                    except Exception as e:
                        st.error(f"Error loading conversation: {str(e)}")
            else:
                st.info("No saved conversations found.")
        else:
            st.info("No saved conversations found. Save a conversation to see it here.")
    else:
        st.info("No conversation history yet. Start a conversation in the Chat Interface tab.")

def render_footer():
    """Render the page footer"""
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This interface uses a multi-agent system to analyze databases and answer questions:
    - **Database Explorer**: Understands database structure, schema, and relationships
    - **Query Specialist**: Crafts efficient database queries to retrieve specific data
    - **Visualization Specialist**: Creates informative data visualizations
    - **Group Chat Manager**: Coordinates the specialists to solve complex problems
    
    Built with Streamlit and powered by OpenAI's language models.
    """)

# CSS file content
def create_css_file():
    """Create the CSS file for styling"""
    css_content = """
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .agent-tag {
        font-size: 0.8rem;
        font-weight: bold;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        margin-right: 0.5rem;
    }
    .agent-explorer {
        background-color: #E3F2FD;
        color: #1565C0;
    }
    .agent-query {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    .agent-viz {
        background-color: #FFF3E0;
        color: #E65100;
    }
    .agent-manager {
        background-color: #F3E5F5;
        color: #6A1B9A;
    }
    .message-container {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #EEEEEE;
    }
    .user-message {
        background-color: #F5F5F5;
    }
    .assistant-message {
        background-color: #FAFAFA;
    }
    .database-form {
        padding: 1rem;
        background-color: #FAFAFA;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
        border-radius: 0.5rem;
    }
    .stButton button:hover {
        background-color: #1565C0;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }
    .chat-input {
        margin-top: 1rem;
    }
    """
    
    # Create the css directory if it doesn't exist
    os.makedirs("css", exist_ok=True)
    
    # Write the CSS file
    with open("style.css", "w") as f:
        f.write(css_content)

# Main entry point
if __name__ == "__main__":
    # Create the CSS file if it doesn't exist
    if not os.path.exists("style.css"):
        create_css_file()
    
    # Run the application
    main()