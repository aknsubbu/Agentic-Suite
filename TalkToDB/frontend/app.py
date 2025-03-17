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
import logging
from bson import json_util

import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mongodb_ui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mongodb_ui")

# Import MongoDB agent system components
from mongoDBExplorer import MongoDBExplorer
from DBAgent import MongoDBAgentSystem
from response_capture import ResponseCapture, patch_agent_system

# Utility function to create a MongoDB explorer
def get_mongodb_explorer(connection_string: str, db_name: str = None) -> MongoDBExplorer:
    """Create a MongoDB explorer with connection string and database name"""
    try:
        if not db_name:
            # Try to extract db_name from connection string if not provided separately
            # MongoDB connection strings typically follow this pattern: mongodb://user:password@host:port/database
            try:
                from urllib.parse import urlparse
                parsed_uri = urlparse(connection_string)
                auto_db_name = parsed_uri.path.strip('/')
                if auto_db_name:
                    db_name = auto_db_name
                    logger.info(f"Extracted database name from connection string: {db_name}")
                else:
                    raise ValueError("Database name is required but could not be extracted from connection string")
            except Exception as e:
                logger.error(f"Error extracting database name: {str(e)}")
                raise ValueError(f"Database name is required: {str(e)}")
                    
        # Create the MongoDB explorer
        logger.info(f"Creating MongoDB explorer for database: {db_name}")
        mongodb_explorer = MongoDBExplorer(db_name=db_name, connection_string=connection_string)
        
        # Test the connection
        if not mongodb_explorer.db_client.ping():
            raise ConnectionError("Could not establish a connection to MongoDB server")
            
        return mongodb_explorer
            
    except Exception as e:
        error_msg = f"Failed to create MongoDB explorer: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        raise e

# Create a custom wrapper for the MongoDBAgentSystem that captures responses for Streamlit UI
class StreamlitMongoDBAgent:
    """A wrapper around MongoDBAgentSystem that captures responses for Streamlit UI"""
    
    def __init__(self, connection_string: str, db_name: str, openai_model: str, openai_key: str):
        """Initialize with MongoDB connection parameters and OpenAI credentials"""
        try:
            # Create the agent system using the new wrapper
            self.agent_system = MongoDBAgentSystem(
                connection_string=connection_string,
                db_name=db_name,
                openai_model=openai_model,
                openai_key=openai_key
            )
            
            # Create response capture
            self.response_capture = ResponseCapture()
            
            # Register the response capture as a listener
            self.agent_system.add_response_listener(self.response_capture)
            
        except Exception as e:
            error_msg = f"Error initializing StreamlitMongoDBAgent: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            raise e
        
    def get_response(self, message: str) -> Dict:
        """Process a message and return the response"""
        try:
            # Clear the previous latest response
            self.response_capture.latest_response = None
            
            # Start the interaction
            logger.info(f"Processing message: {message[:50]}...")
            self.agent_system.start_interaction(message)
            
            # Return the captured response
            if self.response_capture.latest_response:
                # Ensure response has the required fields
                response = self.response_capture.latest_response
                if "role" not in response:
                    response["role"] = "assistant"
                    
                logger.info(f"Response received from agent: {response.get('agent', 'Unknown')}")
                return response
            else:
                # If no response was captured, create a default one
                logger.warning("No response was captured from the agent system")
                return {
                    "agent": "System",
                    "content": "I processed your request but didn't generate a specific response.",
                    "role": "assistant",
                    "type": "text",
                    "time": datetime.now().strftime("%H:%M:%S")
                }
                
        except Exception as e:
            # Log the full error for debugging
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            
            # Return an error response
            return {
                "agent": "System",
                "content": f"Error processing message: {str(e)}",
                "role": "assistant",
                "type": "text",
                "time": datetime.now().strftime("%H:%M:%S")
            }

# Main application function
def main():
    # Set page configuration
    st.set_page_config(
        page_title="MongoDB AI Agent",
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
    if 'db_name' not in st.session_state:
        st.session_state.db_name = None
    if 'connection_string' not in st.session_state:
        st.session_state.connection_string = None
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if 'api_key_valid' not in st.session_state:
        st.session_state.api_key_valid = False
    
    # Main header
    st.markdown('<h1 class="main-header">🤖 MongoDB AI Agent</h1>', unsafe_allow_html=True)
    st.markdown('An intelligent multi-agent system for MongoDB database exploration, analysis, and visualization.')
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["MongoDB Connection", "Chat Interface", "History"])
    
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

def render_connection_tab():
    """Render the MongoDB connection tab"""
    st.markdown('<h2 class="sub-header">MongoDB Connection</h2>', unsafe_allow_html=True)
    
    # Database configuration form
    with st.form(key='mongodb_form', clear_on_submit=False):
        st.markdown('<div class="database-form">', unsafe_allow_html=True)
        
        # MongoDB connection info
        st.markdown("#### MongoDB Connection Information")
        
        connection_string = st.text_input(
            "MongoDB Connection String", 
            placeholder="mongodb://username:password@localhost:27017/database_name",
            help="Example: mongodb://localhost:27017/mydatabase or mongodb+srv://username:password@cluster.mongodb.net/database"
        )
        
        db_name = st.text_input(
            "Database Name (leave blank to extract from connection string)",
            help="The name of the MongoDB database to connect to"
        )
        
        # Add info about connection strings
        with st.expander("MongoDB Connection String Help"):
            st.markdown("""
            **MongoDB Connection String Format:**
            ```
            mongodb://[username:password@]host[:port]/database[?options]
            ```
            
            **Atlas Connection String Format:**
            ```
            mongodb+srv://[username:password@]cluster.example.com/database[?options]
            ```
            
            **Examples:**
            - Simple connection: `mongodb://localhost:27017/mydatabase`
            - With authentication: `mongodb://myusername:mypassword@localhost:27017/mydatabase`
            - Atlas connection: `mongodb+srv://username:password@cluster.mongodb.net/mydatabase`
            - Multiple hosts (replica set): `mongodb://host1:27017,host2:27017/mydatabase?replicaSet=myrs`
            """)
            
            st.markdown("""
            **Important Security Notes:**
            - The connection string should include the database name
            - For Atlas connections, use the connection string from the Atlas dashboard
            - Use a read-only user if possible for security
            """)
        
        # Connection options
        st.markdown("#### Connection Options")
        
        connect_timeout = st.slider(
            "Connection Timeout (seconds)",
            min_value=5,
            max_value=60,
            value=30,
            help="Timeout for MongoDB connection attempts"
        )
        
        # OpenAI Configuration
        st.markdown("#### OpenAI Configuration")
        col1, col2 = st.columns(2)
        with col1:
            openai_model = st.selectbox(
                "OpenAI Model",
                ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "gpt-4o-mini"],
                index=4,  # Default to gpt-4o-mini as it's most cost-effective
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
        submit_button = st.form_submit_button(label="Connect to MongoDB")
        
        if submit_button:
            # Validate inputs
            if not connection_string:
                st.error("MongoDB connection string is required")
            elif not (db_name or "/" in connection_string):
                st.error("Either provide a database name or include it in the connection string")
            elif not openai_key:
                st.error("OpenAI API Key is required")
            else:
                with st.spinner("Connecting to MongoDB..."):
                    try:
                        # Store connection parameters in session state
                        st.session_state.connection_string = connection_string
                        st.session_state.db_name = db_name
                        
                        # Create agent system directly with connection string and db_name
                        agent_system = StreamlitMongoDBAgent(
                            connection_string=connection_string,
                            db_name=db_name,
                            openai_model=openai_model,
                            openai_key=openai_key
                        )
                        
                        # Store the agent in session state
                        st.session_state.agent = agent_system
                        
                        # Set connection flags
                        st.session_state.db_connected = True
                        st.session_state.api_key_valid = True
                        
                        # Add database name to session state
                        if db_name:
                            display_db_name = db_name
                        else:
                            # Extract from connection string
                            from urllib.parse import urlparse
                            parsed_uri = urlparse(connection_string)
                            display_db_name = parsed_uri.path.strip('/')
                        
                        st.success(f"Successfully connected to MongoDB database: {display_db_name}")
                        
                        # Add initial system message
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"Connected to MongoDB database: {display_db_name}. I'm ready to help you explore and analyze your MongoDB data!",
                            "type": "text",
                            "time": datetime.now().strftime("%H:%M:%S")
                        })
                        
                    except Exception as e:
                        st.error(f"Failed to connect to MongoDB: {str(e)}")
                        
                        # Show more detailed error information in an expander
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())
    
    # Connection status indicator
    st.markdown("### Connection Status")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.db_connected:
            st.success("✅ Connected to MongoDB")
            
            # Show connection info
            if st.session_state.db_name:
                st.info(f"Database: {st.session_state.db_name}")
        else:
            st.error("❌ Not Connected to MongoDB")
    with col2:
        if st.session_state.api_key_valid:
            st.success("✅ OpenAI API Key Valid")
        else:
            st.error("❌ OpenAI API Key Not Verified")
            
    # Connection test button (to verify connection is still active)
    if st.session_state.db_connected and st.button("Test MongoDB Connection"):
        try:
            # Get connection status using the agent
            status_message = st.session_state.agent.get_response("Check the MongoDB connection status")
            
            if "error" in status_message.get("content", "").lower():
                st.error(status_message.get("content"))
                st.session_state.db_connected = False
            else:
                st.success("MongoDB connection is active")
                
        except Exception as e:
            st.error(f"Connection test failed: {str(e)}")
            st.session_state.db_connected = False


def render_chat_tab():
    """Render the chat interface tab"""
    st.markdown('<h2 class="sub-header">MongoDB Chat Interface</h2>', unsafe_allow_html=True)
    
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
                
                if agent_name == "MongoDBExplorer":
                    agent_class = "agent-explorer"
                    agent_display = "MongoDB Explorer"
                elif agent_name == "MongoDBQuerySpecialist":
                    agent_class = "agent-query"
                    agent_display = "Query Specialist"
                elif agent_name == "MongoDBVisualizationSpecialist":
                    agent_class = "agent-viz"
                    agent_display = "Viz Specialist"
                elif agent_name == "GroupChatManager":
                    agent_class = "agent-manager"
                    agent_display = "Manager"
                else:
                    agent_class = "agent-system"
                    agent_display = "System"
                
                # Start the message container
                st.markdown(f'<div class="message-container assistant-message">'
                          f'<span class="agent-tag {agent_class}">{agent_display}</span>'
                          f'<strong>Assistant ({message["time"]}):</strong><br/>{message["content"]}'
                          f'</div>', unsafe_allow_html=True)
                
                # If the message contains data, display it
                if message.get("type") == "data" and "data" in message:
                    with st.expander("View MongoDB Data", expanded=True):
                        st.dataframe(message["data"])
                        
                        # Add export buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            csv = message["data"].to_csv(index=False)
                            b64 = base64.b64encode(csv.encode()).decode()
                            href = f'<a href="data:file/csv;base64,{b64}" download="mongodb_data.csv">Download CSV</a>'
                            st.markdown(href, unsafe_allow_html=True)
                        with col2:
                            excel_buffer = BytesIO()
                            message["data"].to_excel(excel_buffer, index=False)
                            excel_buffer.seek(0)
                            b64 = base64.b64encode(excel_buffer.getvalue()).decode()
                            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="mongodb_data.xlsx">Download Excel</a>'
                            st.markdown(href, unsafe_allow_html=True)
                        with col3:
                            # Use json_util for proper BSON type serialization
                            json_str = json.dumps(
                                message["data"].to_dict(orient="records"), 
                                default=json_util.default
                            )
                            b64 = base64.b64encode(json_str.encode()).decode()
                            href = f'<a href="data:file/json;base64,{b64}" download="mongodb_data.json">Download JSON</a>'
                            st.markdown(href, unsafe_allow_html=True)
                
                # If the message contains a visualization, display it
                if message.get("type") == "visualization" and "visualization" in message:
                    with st.expander("View MongoDB Visualization", expanded=True):
                        st.plotly_chart(message["visualization"], use_container_width=True)
                        
                        # Add download button for the visualization
                        buf = BytesIO()
                        message["visualization"].write_image(buf, format="png")
                        buf.seek(0)
                        b64 = base64.b64encode(buf.getvalue()).decode()
                        href = f'<a href="data:image/png;base64,{b64}" download="mongodb_visualization.png">Download Visualization as PNG</a>'
                        st.markdown(href, unsafe_allow_html=True)
    
    # Chat input
    if st.session_state.db_connected:
        # Message input
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        
        with st.form(key='message_form', clear_on_submit=True):
            user_input = st.text_area("Type your message about MongoDB:", height=100, 
                                     help="Ask questions about your MongoDB database, collections, documents, or request analyses")
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
            with st.spinner("Analyzing MongoDB..."):
                try:
                    # Get response from agent system
                    response = st.session_state.agent.get_response(user_input)
                    
                    # Add agent response to chat
                    st.session_state.messages.append(response)
                    
                    # Rerun to update the UI with the new messages
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Error processing MongoDB request: {str(e)}"
                    logger.error(error_msg)
                    st.error(error_msg)
                    
                    # Add error message to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "agent": "System",
                        "content": f"Error: {str(e)}",
                        "type": "text",
                        "time": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Rerun to update the UI
                    st.rerun()
                
        # Suggested MongoDB queries to help users get started
        if len(st.session_state.messages) <= 1:  # Only show suggestions at the beginning
            st.markdown("### Suggested MongoDB Queries")
            suggestion_cols = st.columns(3)
            
            suggestions = [
                "Explore the MongoDB database structure",
                "Show me all collections and document counts",
                "Find the most common field values across collections"
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
                        with st.spinner("Analyzing MongoDB..."):
                            try:
                                # Get response from agent system
                                response = st.session_state.agent.get_response(suggestion)
                                
                                # Add agent response to chat
                                st.session_state.messages.append(response)
                                
                                # Rerun to update the UI
                                st.rerun()
                                
                            except Exception as e:
                                error_msg = f"Error processing MongoDB request: {str(e)}"
                                logger.error(error_msg)
                                
                                # Add error message to chat
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "agent": "System",
                                    "content": f"Error: {str(e)}",
                                    "type": "text",
                                    "time": datetime.now().strftime("%H:%M:%S")
                                })
                                
                                # Rerun to update the UI
                                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please connect to a MongoDB database first in the Connection tab.")

def render_history_tab():
    """Render the conversation history tab"""
    st.markdown('<h2 class="sub-header">MongoDB Conversation History</h2>', unsafe_allow_html=True)
    
    # Conversation management
    if len(st.session_state.messages) > 0:
        # Allow saving the conversation
        st.markdown("### Save Current MongoDB Conversation")
        save_name = st.text_input("Conversation Name", f"MongoDB-{st.session_state.conversation_id[:8]}")
        
        if st.button("Save Conversation"):
            # Create a directory for saved conversations if it doesn't exist
            os.makedirs("mongodb_conversations", exist_ok=True)
            
            # Prepare the conversation data
            conversation_data = {
                "id": st.session_state.conversation_id,
                "name": save_name,
                "timestamp": datetime.now().isoformat(),
                "database": st.session_state.db_name or "Unknown",
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
            filename = f"mongodb_conversations/{save_name}_{st.session_state.conversation_id}.json"
            with open(filename, "w") as f:
                json.dump(conversation_data, f, indent=2, default=json_util.default)
                
            st.success(f"MongoDB conversation '{save_name}' saved successfully to {filename}!")
        
        # Allow clearing the conversation
        if st.button("Clear Current Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_id = str(uuid.uuid4())
            st.rerun()
        
        # Option to export conversation
        st.markdown("### Export MongoDB Conversation")
        export_format = st.selectbox("Export Format", ["JSON", "Text", "HTML"])
        
        if st.button("Export"):
            with st.spinner("Preparing MongoDB conversation export..."):
                if export_format == "JSON":
                    # Convert to JSON
                    export_data = []
                    for msg in st.session_state.messages:
                        # Create a copy without any visualizations or dataframes
                        msg_copy = {k: v for k, v in msg.items() 
                                  if k not in ["visualization", "data"]}
                        export_data.append(msg_copy)
                        
                    json_str = json.dumps(export_data, indent=2, default=json_util.default)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    href = f'<a href="data:file/json;base64,{b64}" download="mongodb_conversation.json">Download JSON</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                elif export_format == "Text":
                    # Convert to text
                    text_lines = []
                    for msg in st.session_state.messages:
                        sender = "You" if msg["role"] == "user" else f"MongoDB Assistant ({msg.get('agent', 'System')})"
                        text_lines.append(f"{sender} ({msg['time']}): {msg['content']}")
                        
                    text_content = "\n\n".join(text_lines)
                    b64 = base64.b64encode(text_content.encode()).decode()
                    href = f'<a href="data:text/plain;base64,{b64}" download="mongodb_conversation.txt">Download Text</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                elif export_format == "HTML":
                    # Convert to HTML
                    html_lines = ["<html><head><title>MongoDB Conversation Export</title>",
                                 "<style>body{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;}",
                                 ".msg{padding:10px;margin:10px 0;border-radius:5px;}",
                                 ".user{background-color:#f0f0f0;}",
                                 ".assistant{background-color:#f8f8f8;}",
                                 ".mongodb{color:#4DB33D;font-weight:bold;}</style></head><body>",
                                 "<h1><span class='mongodb'>MongoDB</span> Conversation Export</h1>"]
                    
                    for msg in st.session_state.messages:
                        css_class = "user" if msg["role"] == "user" else "assistant"
                        sender = "You" if msg["role"] == "user" else "MongoDB Assistant"
                        agent = f" ({msg.get('agent', 'System')})" if msg["role"] == "assistant" else ""
                        
                        html_lines.append(f'<div class="msg {css_class}">')
                        html_lines.append(f'<strong>{sender}{agent} ({msg["time"]}):</strong><br/>')
                        html_lines.append(f'{msg["content"]}')
                        html_lines.append('</div>')
                        
                    html_lines.append("</body></html>")
                    html_content = "\n".join(html_lines)
                    b64 = base64.b64encode(html_content.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="mongodb_conversation.html">Download HTML</a>'
                    st.markdown(href, unsafe_allow_html=True)
        
        # Show saved conversations
        st.markdown("### Saved MongoDB Conversations")
        if os.path.exists("mongodb_conversations"):
            saved_files = [f for f in os.listdir("mongodb_conversations") if f.endswith(".json")]
            
            if saved_files:
                saved_conversations = []
                
                for file in saved_files:
                    try:
                        with open(f"mongodb_conversations/{file}", "r") as f:
                            data = json.load(f)
                            saved_conversations.append({
                                "filename": file,
                                "name": data.get("name", file),
                                "database": data.get("database", "Unknown"),
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
                    "database": "MongoDB Database",
                    "timestamp": "Saved On",
                    "message_count": "Messages"
                })
                
                st.dataframe(saved_df[["Conversation Name", "MongoDB Database", "Saved On", "Messages"]])
                
                # Allow loading a conversation
                selected_conversation = st.selectbox(
                    "Select a MongoDB conversation to load:",
                    options=[conv["filename"] for conv in saved_conversations],
                    format_func=lambda x: next((c["name"] for c in saved_conversations if c["filename"] == x), x)
                )
                
                if st.button("Load Selected Conversation"):
                    try:
                        with open(f"mongodb_conversations/{selected_conversation}", "r") as f:
                            data = json.load(f)
                            
                            # Replace current conversation
                            st.session_state.messages = data.get("messages", [])
                            st.session_state.conversation_id = data.get("id", str(uuid.uuid4()))
                            
                            st.success(f"Loaded MongoDB conversation '{data.get('name')}' for database '{data.get('database')}'")
                            st.experimental_rerun()
                            
                    except Exception as e:
                        st.error(f"Error loading MongoDB conversation: {str(e)}")
            else:
                st.info("No saved MongoDB conversations found.")
        else:
            st.info("No saved MongoDB conversations found. Save a conversation to see it here.")
    else:
        st.info("No MongoDB conversation history yet. Start a conversation in the Chat Interface tab.")

def render_footer():
    """Render the page footer"""
    st.markdown("---")
    st.markdown("### About MongoDB AI Agent")
    st.markdown("""
    This interface uses a specialized multi-agent system to analyze MongoDB databases and answer questions:
    - **MongoDB Explorer**: Understands MongoDB collections, documents, and relationships
    - **MongoDB Query Specialist**: Crafts efficient MongoDB queries and aggregation pipelines
    - **MongoDB Visualization Specialist**: Creates informative data visualizations from MongoDB data
    - **Group Chat Manager**: Coordinates the specialists to solve complex MongoDB problems
    
    Built with Streamlit and powered by OpenAI's language models.
    """)
    
    # Include MongoDB logo and info
    st.markdown("""
    <div style="display: flex; align-items: center; margin-top: 20px;">
        <div style="margin-right: 20px;">
            <img src="https://www.mongodb.com/assets/images/global/leaf.png" width="50" alt="MongoDB Logo">
        </div>
        <div>
            <p>MongoDB® is a registered trademark of MongoDB, Inc.</p>
            <p>This tool is designed for MongoDB database exploration and analysis.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# CSS file content
def create_css_file():
    """Create the CSS file for styling with MongoDB green color scheme"""
    css_content = """
    .main-header {
        font-size: 2.5rem;
        color: #4DB33D;  /* MongoDB green */
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
    .agent-system {
        background-color: #F1F8E9;
        color: #4DB33D;  /* MongoDB green */
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
        background-color: #4DB33D;  /* MongoDB green */
        color: white;
        border-radius: 0.5rem;
    }
    .stButton button:hover {
        background-color: #3D9330;  /* Darker MongoDB green */
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }
    .chat-input {
        margin-top: 1rem;
    }
    .mongodb-logo {
        color: #4DB33D;
        font-weight: bold;
    }
    a {
        color: #4DB33D !important;  /* MongoDB green for links */
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #4DB33D !important;  /* MongoDB green for tab highlight */
    }
    .stTabs [aria-selected="true"] {
        color: #4DB33D !important;  /* MongoDB green for selected tab */
    }
    """
    
    # Create the css directory if it doesn't exist
    os.makedirs("css", exist_ok=True)
    
    # Write the CSS file
    with open("style.css", "w") as f:
        f.write(css_content)

# Main entry point
if __name__ == "__main__":
    try:
        # Create the CSS file if it doesn't exist
        if not os.path.exists("style.css"):
            create_css_file()
        
        # Run the application
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Application error: {str(e)}")
        traceback.print_exc()