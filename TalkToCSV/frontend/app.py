# """Streamlit frontend for CSV Conversation Agent."""

# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# import requests
# import json
# import base64
# import io
# import os
# import time
# from typing import Dict, List, Any, Optional, Tuple

# # Constants
# API_URL = os.environ.get("API_URL", "http://localhost:8000")
# CHUNK_SIZE = 1 * 1024 * 1024  # 1MB chunk size

# # Configure page
# st.set_page_config(
#     page_title="CSV Conversation Agent",
#     page_icon="📊",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Functions for API communication
# def upload_csv_in_chunks(file) -> Dict[str, Any]:
#     """Upload a CSV file in chunks to the API.
    
#     Args:
#         file: File object from st.file_uploader
        
#     Returns:
#         API response for the final chunk
#     """
#     file_size = file.size
#     chunk_count = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE  # Ceiling division
    
#     file_id = None
    
#     with st.spinner(f"Uploading file in {chunk_count} chunks..."):
#         progress_bar = st.progress(0)
        
#         for i in range(chunk_count):
#             # Seek to the correct position
#             file.seek(i * CHUNK_SIZE)
            
#             # Read the chunk
#             chunk_data = file.read(CHUNK_SIZE)
            
#             # Determine if this is the last chunk
#             is_last = i == chunk_count - 1
            
#             # Prepare request data
#             data = {
#                 "chunk_number": i,
#                 "total_chunks": chunk_count,
#                 "data": base64.b64encode(chunk_data).decode('utf-8'),
#                 "is_last": is_last,
#                 "filename": file.name
#             }
            
#             # If we have a file_id from a previous chunk, include it
#             if file_id:
#                 data["file_id"] = file_id
            
#             # Send the chunk
#             response = requests.post(f"{API_URL}/upload/chunk", json=data)
            
#             if response.status_code != 200:
#                 st.error(f"Error uploading chunk {i}: {response.text}")
#                 return None
            
#             # Get the file_id from the first chunk response
#             response_data = response.json()
#             if i == 0:
#                 file_id = response_data.get("file_id")
            
#             # Update progress
#             progress_bar.progress((i + 1) / chunk_count)
            
#             # If this is the last chunk, return the full response
#             if is_last:
#                 return response_data
    
#     return None

# def upload_small_file(file) -> Dict[str, Any]:
#     """Upload a small CSV file directly to the API.
    
#     Args:
#         file: File object from st.file_uploader
        
#     Returns:
#         API response
#     """
#     with st.spinner("Uploading file..."):
#         files = {"file": (file.name, file, "text/csv")}
#         response = requests.post(f"{API_URL}/upload/file", files=files)
        
#         if response.status_code != 200:
#             st.error(f"Error uploading file: {response.text}")
#             return None
        
#         return response.json()

# def get_file_analysis(file_id: str) -> Dict[str, Any]:
#     """Get comprehensive analysis of a CSV file.
    
#     Args:
#         file_id: ID of the uploaded file
        
#     Returns:
#         Analysis data from API
#     """
#     with st.spinner("Generating analysis..."):
#         response = requests.get(f"{API_URL}/files/{file_id}/analysis")
        
#         if response.status_code != 200:
#             st.error(f"Error getting analysis: {response.text}")
#             return None
        
#         return response.json()

# def query_csv(file_id: str, query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
#     """Send a natural language query to the API.
    
#     Args:
#         file_id: ID of the uploaded file
#         query: Natural language query
#         conversation_id: Optional conversation ID for continuing a conversation
        
#     Returns:
#         Query results from API
#     """
#     with st.spinner("Processing query..."):
#         data = {
#             "file_id": file_id,
#             "query": query
#         }
        
#         if conversation_id:
#             data["conversation_id"] = conversation_id
        
#         response = requests.post(f"{API_URL}/query", json=data)
        
#         if response.status_code != 200:
#             st.error(f"Error processing query: {response.text}")
#             try:
#                 return response.json()
#             except:
#                 return {"error": response.text}
        
#         return response.json()

# # Functions for visualization
# def create_visualization(data: Dict[str, Any], visualization_type: str) -> Optional[Any]:
#     """Create a visualization based on the result data and type.
    
#     Args:
#         data: Result data from query
#         visualization_type: Type of visualization to create
        
#     Returns:
#         Plotly figure or None
#     """
#     if not data or not visualization_type or visualization_type == "none":
#         return None
    
#     # Handle different result types
#     if isinstance(data, dict) and "type" in data:
#         # Process based on result type
#         if data["type"] == "dataframe":
#             df = pd.DataFrame(data["data"])
#             return visualize_dataframe(df, visualization_type)
        
#         elif data["type"] == "series":
#             # Convert series to DataFrame for visualization
#             series_data = data["data"]
#             index = data["index"]
#             df = pd.DataFrame({
#                 "index": index,
#                 data["name"] if data["name"] else "value": list(series_data.values())
#             })
#             return visualize_dataframe(df, visualization_type)
        
#         elif data["type"] == "figure" and "data" in data:
#             # Image data is already provided
#             return data["data"]
    
#     # If we reach here, try to convert to DataFrame
#     try:
#         if isinstance(data, list):
#             df = pd.DataFrame(data)
#             return visualize_dataframe(df, visualization_type)
#     except:
#         pass
    
#     return None

# def visualize_dataframe(df: pd.DataFrame, visualization_type: str) -> Optional[Any]:
#     """Create a visualization from a DataFrame.
    
#     Args:
#         df: Pandas DataFrame
#         visualization_type: Type of visualization to create
        
#     Returns:
#         Plotly figure or None
#     """
#     if df.empty:
#         return None
    
#     try:
#         # Bar chart
#         if visualization_type == "bar":
#             if len(df.columns) >= 2:
#                 x_col = df.columns[0]
#                 y_col = df.columns[1]
#                 return px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
#             return px.bar(df, title="Bar Chart")
        
#         # Line chart
#         elif visualization_type == "line":
#             if len(df.columns) >= 2:
#                 x_col = df.columns[0]
#                 y_col = df.columns[1]
#                 return px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
#             return px.line(df, title="Line Chart")
        
#         # Scatter plot
#         elif visualization_type == "scatter":
#             if len(df.columns) >= 2:
#                 x_col = df.columns[0]
#                 y_col = df.columns[1]
#                 return px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
#             return None
        
#         # Histogram
#         elif visualization_type == "histogram":
#             if len(df.columns) >= 1:
#                 x_col = df.columns[0]
#                 return px.histogram(df, x=x_col, title=f"Distribution of {x_col}")
#             return None
        
#         # Box plot
#         elif visualization_type == "box":
#             if len(df.columns) >= 1:
#                 y_col = df.select_dtypes(include=np.number).columns[0] if not df.select_dtypes(include=np.number).empty else df.columns[0]
#                 return px.box(df, y=y_col, title=f"Distribution of {y_col}")
#             return None
        
#         # Pie chart
#         elif visualization_type == "pie":
#             if len(df.columns) >= 2:
#                 names_col = df.columns[0]
#                 values_col = df.select_dtypes(include=np.number).columns[0] if not df.select_dtypes(include=np.number).empty else df.columns[1]
#                 return px.pie(df, names=names_col, values=values_col, title=f"{values_col} by {names_col}")
#             return None
        
#         # Heatmap
#         elif visualization_type == "heatmap":
#             # For heatmaps, we need the DataFrame to be in the right format (numeric values with row/column indices)
#             if len(df.columns) >= 3:  # Need at least 3 columns for a meaningful heatmap
#                 try:
#                     # Pivot the data if possible
#                     pivot_cols = df.columns[:3]
#                     pivot_df = df.pivot(index=pivot_cols[0], columns=pivot_cols[1], values=pivot_cols[2])
#                     return px.imshow(pivot_df, title=f"Heatmap of {pivot_cols[2]}")
#                 except:
#                     # If pivot fails, just use the DataFrame as is
#                     return px.imshow(df.select_dtypes(include=np.number), title="Heatmap")
#             elif not df.select_dtypes(include=np.number).empty:
#                 return px.imshow(df.select_dtypes(include=np.number), title="Heatmap")
#             return None
        
#         # Default to table view (not a visualization)
#         return None
    
#     except Exception as e:
#         st.error(f"Error creating visualization: {str(e)}")
#         return None

# # Session state initialization
# if "file_id" not in st.session_state:
#     st.session_state.file_id = None

# if "file_metadata" not in st.session_state:
#     st.session_state.file_metadata = None

# if "conversation_id" not in st.session_state:
#     st.session_state.conversation_id = None

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# if "csv_data" not in st.session_state:
#     st.session_state.csv_data = None

# if "analysis" not in st.session_state:
#     st.session_state.analysis = None

# # App title
# st.title("CSV Conversation Agent 📊")

# # Sidebar for file upload and metadata
# with st.sidebar:
#     st.header("Upload CSV File")
    
#     uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    
#     if uploaded_file is not None:
#         # Check if this is a new file
#         file_details = {"filename": uploaded_file.name, "size": uploaded_file.size}
        
#         # Only process if file has changed or no file is loaded
#         if not st.session_state.file_id or st.session_state.file_metadata.get("filename") != file_details["filename"]:
#             # Handle file upload based on size
#             if uploaded_file.size > 5 * 1024 * 1024:  # 5MB threshold
#                 result = upload_csv_in_chunks(uploaded_file)
#             else:
#                 result = upload_small_file(uploaded_file)
            
#             if result and result.get("status") == "success":
#                 st.session_state.file_id = result.get("file_id")
#                 st.session_state.file_metadata = result.get("metadata")
#                 st.session_state.analysis = result.get("analysis")
                
#                 # Reset conversation on new file
#                 st.session_state.conversation_id = None
#                 st.session_state.messages = []
                
#                 # Read the CSV data for display
#                 uploaded_file.seek(0)
#                 st.session_state.csv_data = pd.read_csv(uploaded_file)
                
#                 st.success(f"File uploaded successfully! {result.get('file_id')}")
#             else:
#                 st.error("File upload failed. Please try again.")
    
#     # Display file metadata if available
#     if st.session_state.file_metadata:
#         st.subheader("File Information")
#         st.write(f"Rows: {st.session_state.file_metadata.get('row_count', 0)}")
#         st.write(f"Columns: {st.session_state.file_metadata.get('column_count', 0)}")
        
#         if st.button("View Detailed Analysis"):
#             if not st.session_state.analysis:
#                 st.session_state.analysis = get_file_analysis(st.session_state.file_id)
            
#             if st.session_state.analysis:
#                 st.json(st.session_state.analysis)

# # Main content area with tabs
# tab1, tab2, tab3 = st.tabs(["Data Explorer", "Analysis Dashboard", "Chat"])

# # Tab 1: Data Explorer
# with tab1:
#     if st.session_state.csv_data is not None:
#         st.header("CSV Data Preview")
        
#         # Display the DataFrame
#         st.dataframe(st.session_state.csv_data, use_container_width=True)
        
#         # Display column information
#         if st.session_state.file_metadata:
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.subheader("Column Names")
#                 st.write(st.session_state.file_metadata.get("columns", []))
            
#             with col2:
#                 st.subheader("Data Types")
#                 st.write(st.session_state.file_metadata.get("dtypes", {}))
#     else:
#         st.info("Please upload a CSV file to begin.")

# # Tab 2: Analysis Dashboard
# with tab2:
#     if st.session_state.analysis is not None:
#         st.header("Automatic Analysis")
        
#         # Display summary statistics
#         if "summary_stats" in st.session_state.analysis:
#             st.subheader("Summary Statistics")
            
#             summary = st.session_state.analysis["summary_stats"]
#             col1, col2, col3 = st.columns(3)
            
#             with col1:
#                 st.metric("Rows", summary.get("row_count", 0))
            
#             with col2:
#                 st.metric("Columns", summary.get("column_count", 0))
            
#             with col3:
#                 st.metric("Numeric Columns", len(summary.get("numeric_columns", [])))
        
#         # Display data quality information
#         if "data_quality" in st.session_state.analysis:
#             st.subheader("Data Quality")
            
#             quality = st.session_state.analysis["data_quality"]
            
#             # Missing values
#             if "missing_values" in quality:
#                 missing = quality["missing_values"]
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.metric("Total Missing Values", missing.get("total_missing", 0))
                
#                 with col2:
#                     st.metric("Missing Percentage", f"{missing.get('missing_percentage', 0):.2f}%")
                
#                 if missing.get("columns_with_missing"):
#                     st.write("Columns with missing values:")
#                     missing_df = pd.DataFrame({
#                         "Column": list(missing["columns_with_missing"].keys()),
#                         "Missing Count": list(missing["columns_with_missing"].values())
#                     })
#                     st.dataframe(missing_df)
            
#             # Duplicates
#             if "duplicates" in quality:
#                 duplicates = quality["duplicates"]
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.metric("Duplicate Rows", duplicates.get("duplicate_rows", 0))
                
#                 with col2:
#                     st.metric("Duplicate Percentage", f"{duplicates.get('duplicate_percentage', 0):.2f}%")
            
#             # Outliers
#             if "outliers" in quality and quality["outliers"]:
#                 st.write("Potential outliers detected:")
                
#                 for col, outlier_info in quality["outliers"].items():
#                     st.write(f"**{col}**: {outlier_info['outlier_count']} outliers ({outlier_info['outlier_percentage']:.2f}%)")
        
#         # Display visualizations
#         if "visualizations" in st.session_state.analysis:
#             st.subheader("Recommended Visualizations")
            
#             viz_list = st.session_state.analysis["visualizations"]
            
#             # Show a selection dropdown for visualizations
#             if viz_list:
#                 viz_options = [f"{v['title']} ({v['type']})" for v in viz_list]
#                 selected_viz = st.selectbox("Select visualization:", viz_options)
                
#                 # Get the selected visualization
#                 selected_index = viz_options.index(selected_viz)
#                 viz_config = viz_list[selected_index]
                
#                 # Create the visualization
#                 if st.session_state.csv_data is not None:
#                     fig = None
                    
#                     if viz_config["type"] == "histogram":
#                         fig = px.histogram(
#                             st.session_state.csv_data,
#                             x=viz_config["config"]["x"],
#                             title=viz_config["title"]
#                         )
                    
#                     elif viz_config["type"] == "bar":
#                         fig = px.bar(
#                             st.session_state.csv_data,
#                             x=viz_config["config"]["x"],
#                             y=viz_config["config"]["y"] if "y" in viz_config["config"] else None,
#                             title=viz_config["title"]
#                         )
                    
#                     elif viz_config["type"] == "line":
#                         fig = px.line(
#                             st.session_state.csv_data,
#                             x=viz_config["config"]["x"],
#                             y=viz_config["config"]["y"],
#                             title=viz_config["title"]
#                         )
                    
#                     elif viz_config["type"] == "scatter":
#                         fig = px.scatter(
#                             st.session_state.csv_data,
#                             x=viz_config["config"]["x"],
#                             y=viz_config["config"]["y"],
#                             title=viz_config["title"]
#                         )
                    
#                     elif viz_config["type"] == "box":
#                         fig = px.box(
#                             st.session_state.csv_data,
#                             y=viz_config["config"]["y"] if "y" in viz_config["config"] else None,
#                             x=viz_config["config"]["x"] if "x" in viz_config["config"] else None,
#                             title=viz_config["title"]
#                         )
                    
#                     if fig:
#                         st.plotly_chart(fig, use_container_width=True)
#                         st.write(viz_config["description"])
#     else:
#         st.info("Please upload a CSV file to see analysis.")

# # Tab 3: Chat Interface
# with tab3:
#     st.header("Chat with your CSV")
    
#     # Display conversation history
#     for message in st.session_state.messages:
#         if message["role"] == "user":
#             st.chat_message("user").write(message["content"])
#         else:
#             with st.chat_message("assistant"):
#                 st.write(message["content"])
                
#                 # Display visualization if available
#                 if "visualization" in message:
#                     viz_type = message.get("visualization_type", "none")
#                     viz_data = message.get("result")
                    
#                     if viz_type != "none" and viz_data:
#                         fig = create_visualization(viz_data, viz_type)
                        
#                         if fig:
#                             if isinstance(fig, str) and fig.startswith("data:image"):
#                                 # Display base64 encoded image
#                                 st.image(fig)
#                             else:
#                                 # Display Plotly figure
#                                 st.plotly_chart(fig, use_container_width=True)
                
#                 # Display code if available
#                 if "code" in message and message["code"]:
#                     with st.expander("View Code"):
#                         st.code(message["code"], language="python")
                
#                 # Display raw result if available
#                 if "result" in message and message["result"]:
#                     with st.expander("View Raw Result"):
#                         st.json(message["result"])
    
#     # Input for new query
#     if st.session_state.file_id:
#         prompt = st.chat_input("Ask a question about your data...")
        
#         if prompt:
#             # Display user message
#             st.chat_message("user").write(prompt)
            
#             # Add to history
#             st.session_state.messages.append({"role": "user", "content": prompt})
            
#             # Process the query
#             response = query_csv(
#                 file_id=st.session_state.file_id,
#                 query=prompt,
#                 conversation_id=st.session_state.conversation_id
#             )
            
#             # Save conversation ID
#             if "conversation_id" in response:
#                 st.session_state.conversation_id = response["conversation_id"]
            
#             # Create response message
#             response_content = response.get("explanation", "")
            
#             if "error" in response and response["error"]:
#                 response_content = f"Error: {response['error']}\n\n{response_content}"
            
#             # Display assistant message
#             with st.chat_message("assistant"):
#                 st.write(response_content)
                
#                 # Display visualization if available
#                 viz_type = response.get("visualization_type", "none")
#                 viz_data = response.get("result")
                
#                 if viz_type != "none" and viz_data:
#                     fig = create_visualization(viz_data, viz_type)
                    
#                     if fig:
#                         if isinstance(fig, str) and fig.startswith("data:image"):
#                             # Display base64 encoded image
#                             st.image(fig)
#                         else:
#                             # Display Plotly figure
#                             st.plotly_chart(fig, use_container_width=True)
                
#                 # Display code if available
#                 if "code" in response and response["code"]:
#                     with st.expander("View Code"):
#                         st.code(response["code"], language="python")
                
#                 # Display raw result if available
#                 if "result" in response and response["result"]:
#                     with st.expander("View Raw Result"):
#                         st.json(response["result"])
            
#             # Add to history
#             st.session_state.messages.append({
#                 "role": "assistant",
#                 "content": response_content,
#                 "code": response.get("code"),
#                 "result": response.get("result"),
#                 "visualization_type": viz_type,
#                 "visualization": fig if 'fig' in locals() else None
#             })
#     else:
#         st.info("Please upload a CSV file to start chatting.")

# # Footer
# st.markdown("---")
# st.markdown("CSV Conversation Agent - Ask questions about your data in natural language")




"""Streamlit frontend for CSV Conversation Agent with improved formatting."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import base64
import io
import os
import time
import re
from typing import Dict, List, Any, Optional, Tuple

# Constants
API_URL = os.environ.get("API_URL", "http://localhost:8000")
CHUNK_SIZE = 1 * 1024 * 1024  # 1MB chunk size

# Set page configuration
st.set_page_config(
    page_title="CSV Conversation Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {padding-top: 2rem;}
    .stTabs [data-baseweb="tab-panel"] {padding-top: 1rem;}
    .chat-message {padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;}
    .user-message {background-color: #f0f2f6;}
    .assistant-message {background-color: #e6f3ff;}
    .metric-card {padding: 1rem; border-radius: 0.5rem; background-color: #f0f2f6; margin-bottom: 1rem;}
    .st-emotion-cache-14qe28s h1 {color: #2c3e50; margin-bottom: 1.5rem;}
    .st-emotion-cache-14qe28s h2 {color: #34495e; margin-top: 2rem;}
    .st-emotion-cache-14qe28s h3 {color: #3498db; margin-top: 1.5rem;}
    
    /* Improve KPI display */
    .kpi-container {display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;}
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        min-width: 150px;
        flex: 1;
    }
    .kpi-label {font-size: 0.9rem; color: #6c757d; margin-bottom: 0.3rem;}
    .kpi-value {font-size: 1.5rem; font-weight: bold; color: #2c3e50;}
</style>
""", unsafe_allow_html=True)

# Functions for API communication
def upload_csv_in_chunks(file) -> Dict[str, Any]:
    """Upload a CSV file in chunks to the API."""
    file_size = file.size
    chunk_count = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE  # Ceiling division
    
    file_id = None
    
    with st.spinner(f"Uploading file in {chunk_count} chunks..."):
        progress_bar = st.progress(0)
        
        for i in range(chunk_count):
            # Seek to the correct position
            file.seek(i * CHUNK_SIZE)
            
            # Read the chunk
            chunk_data = file.read(CHUNK_SIZE)
            
            # Determine if this is the last chunk
            is_last = i == chunk_count - 1
            
            # Prepare request data
            data = {
                "chunk_number": i,
                "total_chunks": chunk_count,
                "data": base64.b64encode(chunk_data).decode('utf-8'),
                "is_last": is_last,
                "filename": file.name
            }
            
            # If we have a file_id from a previous chunk, include it
            if file_id:
                data["file_id"] = file_id
            
            # Send the chunk
            response = requests.post(f"{API_URL}/upload/chunk", json=data)
            
            if response.status_code != 200:
                st.error(f"Error uploading chunk {i}: {response.text}")
                return None
            
            # Get the file_id from the first chunk response
            response_data = response.json()
            if i == 0:
                file_id = response_data.get("file_id")
            
            # Update progress
            progress_bar.progress((i + 1) / chunk_count)
            
            # If this is the last chunk, return the full response
            if is_last:
                return response_data
    
    return None

def upload_small_file(file) -> Dict[str, Any]:
    """Upload a small CSV file directly to the API."""
    with st.spinner("Uploading file..."):
        files = {"file": (file.name, file, "text/csv")}
        response = requests.post(f"{API_URL}/upload/file", files=files)
        
        if response.status_code != 200:
            st.error(f"Error uploading file: {response.text}")
            return None
        
        return response.json()

def get_file_analysis(file_id: str) -> Dict[str, Any]:
    """Get comprehensive analysis of a CSV file."""
    with st.spinner("Generating analysis..."):
        response = requests.get(f"{API_URL}/files/{file_id}/analysis")
        
        if response.status_code != 200:
            st.error(f"Error getting analysis: {response.text}")
            return None
        
        return response.json()

def query_csv(file_id: str, query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Send a natural language query to the API."""
    with st.spinner("Processing query..."):
        data = {
            "file_id": file_id,
            "query": query
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        response = requests.post(f"{API_URL}/query", json=data)
        
        if response.status_code != 200:
            st.error(f"Error processing query: {response.text}")
            try:
                return response.json()
            except:
                return {"error": response.text}
        
        return response.json()

# Functions for formatting and visualization
def format_explanation(explanation: str) -> str:
    """Format the explanation text for better readability.
    
    Args:
        explanation: The raw explanation text
    
    Returns:
        Formatted explanation with proper spacing and markup
    """
    if not explanation:
        return ""
    
    # Split into paragraphs and make sure there's proper spacing
    paragraphs = re.split(r'\n\s*\n', explanation)
    
    # Fix issues with incorrectly concatenated text (common in the KPI responses)
    formatted_paragraphs = []
    for para in paragraphs:
        # Fix text that's run together with asterisks (like "value.TheaveragetransactionvaluewasX.*value*")
        para = re.sub(r'(\w+)\.(\w+)', r'\1. \2', para)
        para = re.sub(r'(\w+)\*(\w+)\*', r'\1 \2', para)
        
        # Add proper spacing around numbers and monetary values
        para = re.sub(r'(\d+)\.(\d+)', r'\1.\2', para)
        para = re.sub(r'(\$)(\d+)', r'\1 \2', para)
        
        # Format any lists that might be in the text
        para = re.sub(r'- ', r'• ', para)
        
        formatted_paragraphs.append(para)
    
    # Combine paragraphs with proper spacing
    formatted_text = "\n\n".join(formatted_paragraphs)
    
    return formatted_text

def extract_kpis(result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract KPI values from results if available.
    
    Args:
        result: The result data
        
    Returns:
        Dictionary of KPI values or None
    """
    kpis = {}
    
    # Check if the result is a dictionary that might contain KPIs
    if isinstance(result, dict):
        # If the result has KPI-specific keys
        for key in ['transaction_count', 'total_amount', 'average_amount', 'max_amount', 'min_amount']:
            if key in result:
                kpis[key] = result[key]
        
        # If there's a 'data' key with DataFrame-like content
        if "type" in result and result["type"] == "dataframe" and "data" in result:
            df_data = result["data"]
            
            # If we have transaction data, compute basic KPIs
            if df_data and len(df_data) > 0 and "Amount" in df_data[0]:
                amounts = [row.get("Amount", 0) for row in df_data if isinstance(row.get("Amount"), (int, float))]
                if amounts:
                    if 'transaction_count' not in kpis:
                        kpis['transaction_count'] = len(amounts)
                    if 'total_amount' not in kpis:
                        kpis['total_amount'] = sum(amounts)
                    if 'average_amount' not in kpis:
                        kpis['average_amount'] = sum(amounts) / len(amounts)
                    if 'max_amount' not in kpis:
                        kpis['max_amount'] = max(amounts)
                    if 'min_amount' not in kpis:
                        kpis['min_amount'] = min(amounts)
    
    return kpis if kpis else None

def display_kpis(kpis: Dict[str, Any]):
    """Display KPIs in a formatted card layout.
    
    Args:
        kpis: Dictionary of KPI values
    """
    if not kpis:
        return
    
    # Create a container for KPIs
    st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
    
    # Display each KPI in a card
    kpi_labels = {
        'transaction_count': 'Transactions',
        'total_amount': 'Total Amount',
        'average_amount': 'Avg. Amount',
        'max_amount': 'Max Amount',
        'min_amount': 'Min Amount'
    }
    
    for key, label in kpi_labels.items():
        if key in kpis:
            value = kpis[key]
            # Format monetary values
            if 'amount' in key and isinstance(value, (int, float)):
                value_str = f"${value:.2f}"
            else:
                value_str = str(value)
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value_str}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)

def create_visualization(data: Dict[str, Any], visualization_type: str) -> Optional[Any]:
    """Create a visualization based on the result data and type."""
    if not data or not visualization_type or visualization_type == "none":
        return None
    
    # Handle different result types
    if isinstance(data, dict) and "type" in data:
        # Process based on result type
        if data["type"] == "dataframe":
            df = pd.DataFrame(data["data"])
            return visualize_dataframe(df, visualization_type)
        
        elif data["type"] == "series":
            # Convert series to DataFrame for visualization
            series_data = data["data"]
            index = data["index"]
            df = pd.DataFrame({
                "index": index,
                "value": list(series_data.values())
            })
            df.rename(columns={"value": data["name"] if data["name"] else "value"}, inplace=True)
            return visualize_dataframe(df, visualization_type)
        
        elif data["type"] == "figure" and "data" in data:
            # Image data is already provided
            return data["data"]
    
    # If we reach here, try to convert to DataFrame
    try:
        if isinstance(data, list):
            df = pd.DataFrame(data)
            return visualize_dataframe(df, visualization_type)
    except:
        pass
    
    return None

def visualize_dataframe(df: pd.DataFrame, visualization_type: str) -> Optional[Any]:
    """Create a visualization from a DataFrame."""
    if df.empty:
        return None
    
    # Add better styling to all plots
    layout_kwargs = {
        "template": "plotly_white",
        "height": 500,
        "margin": {"t": 50, "b": 50, "l": 50, "r": 50},
    }
    
    try:
        # Bar chart
        if visualization_type == "bar":
            if len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}", **layout_kwargs)
                fig.update_traces(marker_color='#3498db')
                return fig
            return px.bar(df, title="Bar Chart", **layout_kwargs)
        
        # Line chart
        elif visualization_type == "line":
            if len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}", **layout_kwargs)
                fig.update_traces(line=dict(color='#2ecc71', width=3))
                return fig
            return px.line(df, title="Line Chart", **layout_kwargs)
        
        # Scatter plot
        elif visualization_type == "scatter":
            if len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}", **layout_kwargs)
                fig.update_traces(marker=dict(color='#9b59b6', size=10))
                return fig
            return None
        
        # Histogram
        elif visualization_type == "histogram":
            if len(df.columns) >= 1:
                x_col = df.columns[0]
                fig = px.histogram(df, x=x_col, title=f"Distribution of {x_col}", **layout_kwargs)
                fig.update_traces(marker_color='#e67e22')
                return fig
            return None
        
        # Box plot
        elif visualization_type == "box":
            if len(df.columns) >= 1:
                y_col = df.select_dtypes(include=np.number).columns[0] if not df.select_dtypes(include=np.number).empty else df.columns[0]
                fig = px.box(df, y=y_col, title=f"Distribution of {y_col}", **layout_kwargs)
                fig.update_traces(marker_color='#1abc9c', line=dict(color='#16a085'))
                return fig
            return None
        
        # Pie chart
        elif visualization_type == "pie":
            if len(df.columns) >= 2:
                names_col = df.columns[0]
                values_col = df.select_dtypes(include=np.number).columns[0] if not df.select_dtypes(include=np.number).empty else df.columns[1]
                fig = px.pie(df, names=names_col, values=values_col, title=f"{values_col} by {names_col}", **layout_kwargs)
                return fig
            return None
        
        # Heatmap
        elif visualization_type == "heatmap":
            # For heatmaps, we need the DataFrame to be in the right format
            if len(df.columns) >= 3:  # Need at least 3 columns for a meaningful heatmap
                try:
                    # Pivot the data if possible
                    pivot_cols = df.columns[:3]
                    pivot_df = df.pivot(index=pivot_cols[0], columns=pivot_cols[1], values=pivot_cols[2])
                    fig = px.imshow(pivot_df, title=f"Heatmap of {pivot_cols[2]}", **layout_kwargs)
                    return fig
                except:
                    # If pivot fails, just use the DataFrame as is
                    fig = px.imshow(df.select_dtypes(include=np.number), title="Heatmap", **layout_kwargs)
                    return fig
            elif not df.select_dtypes(include=np.number).empty:
                fig = px.imshow(df.select_dtypes(include=np.number), title="Heatmap", **layout_kwargs)
                return fig
            return None
        
        # Default to table view (not a visualization)
        return None
    
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None

# Session state initialization
if "file_id" not in st.session_state:
    st.session_state.file_id = None

if "file_metadata" not in st.session_state:
    st.session_state.file_metadata = None

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "csv_data" not in st.session_state:
    st.session_state.csv_data = None

if "analysis" not in st.session_state:
    st.session_state.analysis = None

# App title with improved styling
st.markdown("<h1 style='text-align: center;'>CSV Conversation Agent 📊</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; margin-bottom: 30px;'>Ask questions about your data in natural language</p>", unsafe_allow_html=True)

# Sidebar for file upload and metadata
with st.sidebar:
    st.header("Upload CSV File")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    
    if uploaded_file is not None:
        # Check if this is a new file
        file_details = {"filename": uploaded_file.name, "size": uploaded_file.size}
        
        # Only process if file has changed or no file is loaded
        if not st.session_state.file_id or st.session_state.file_metadata.get("filename") != file_details["filename"]:
            # Handle file upload based on size
            if uploaded_file.size > 5 * 1024 * 1024:  # 5MB threshold
                result = upload_csv_in_chunks(uploaded_file)
            else:
                result = upload_small_file(uploaded_file)
            
            if result and result.get("status") == "success":
                st.session_state.file_id = result.get("file_id")
                st.session_state.file_metadata = result.get("metadata")
                st.session_state.analysis = result.get("analysis")
                
                # Reset conversation on new file
                st.session_state.conversation_id = None
                st.session_state.messages = []
                
                # Read the CSV data for display
                uploaded_file.seek(0)
                st.session_state.csv_data = pd.read_csv(uploaded_file)
                
                st.success(f"File uploaded successfully!")
            else:
                st.error("File upload failed. Please try again.")
    
    # Display file metadata if available
    if st.session_state.file_metadata:
        st.markdown("---")
        st.subheader("File Information")
        
        # Show file metadata in a cleaner way
        file_info_cols = st.columns(2)
        with file_info_cols[0]:
            st.metric("Rows", st.session_state.file_metadata.get("row_count", 0))
        with file_info_cols[1]:
            st.metric("Columns", st.session_state.file_metadata.get("column_count", 0))
        
        if st.button("View Detailed Analysis", key="btn_analysis"):
            if not st.session_state.analysis:
                st.session_state.analysis = get_file_analysis(st.session_state.file_id)
            
            if st.session_state.analysis:
                # Show a more user-friendly version of the analysis
                st.markdown("### Analysis Overview")
                if "summary_stats" in st.session_state.analysis:
                    summary = st.session_state.analysis["summary_stats"]
                    st.write(f"📊 {len(summary.get('numeric_columns', []))} numeric columns")
                    st.write(f"📝 {len(summary.get('categorical_columns', []))} categorical columns")
                
                # Add a collapsible section for the full JSON
                with st.expander("View Full Analysis JSON"):
                    st.json(st.session_state.analysis)

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Data Explorer", "Analysis Dashboard", "Chat"])

# Tab 1: Data Explorer
with tab1:
    if st.session_state.csv_data is not None:
        st.header("CSV Data Preview")
        
        # Display the DataFrame with improved styling
        st.dataframe(
            st.session_state.csv_data.style.highlight_max(axis=0, color='lightgreen').highlight_min(axis=0, color='lightblue'),
            use_container_width=True
        )
        
        # Display column information in a more organized way
        if st.session_state.file_metadata:
            cols = st.columns(2)
            with cols[0]:
                st.subheader("Column Names")
                col_list = st.session_state.file_metadata.get("columns", [])
                for col in col_list:
                    st.write(f"• {col}")
            
            with cols[1]:
                st.subheader("Data Types")
                dtypes = st.session_state.file_metadata.get("dtypes", {})
                for col, dtype in dtypes.items():
                    st.write(f"• {col}: `{dtype}`")
    else:
        st.info("Please upload a CSV file to begin exploring your data.")

# Tab 2: Analysis Dashboard
with tab2:
    if st.session_state.analysis is not None:
        st.header("Automatic Analysis")
        
        # Display summary statistics with better formatting
        if "summary_stats" in st.session_state.analysis:
            st.subheader("Summary Statistics")
            
            summary = st.session_state.analysis["summary_stats"]
            
            # Display metrics in a cleaner grid
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("Rows", summary.get("row_count", 0))
            with metric_cols[1]:
                st.metric("Columns", summary.get("column_count", 0))
            with metric_cols[2]:
                st.metric("Numeric Columns", len(summary.get("numeric_columns", [])))
            
            # Show column details in expandable sections
            if "column_stats" in summary:
                # Group columns by type
                numeric_cols = summary.get("numeric_columns", [])
                cat_cols = summary.get("categorical_columns", [])
                
                if numeric_cols:
                    with st.expander("Numeric Column Statistics", expanded=True):
                        for col in numeric_cols:
                            if col in summary["column_stats"]:
                                stats = summary["column_stats"][col]
                                st.markdown(f"#### {col}")
                                
                                # Display numeric stats in cleaner format
                                stat_cols = st.columns(5)
                                if "min" in stats:
                                    stat_cols[0].metric("Min", f"{stats['min']:.2f}" if isinstance(stats['min'], float) else stats['min'])
                                if "max" in stats:
                                    stat_cols[1].metric("Max", f"{stats['max']:.2f}" if isinstance(stats['max'], float) else stats['max'])
                                if "mean" in stats:
                                    stat_cols[2].metric("Mean", f"{stats['mean']:.2f}" if isinstance(stats['mean'], float) else stats['mean'])
                                if "median" in stats:
                                    stat_cols[3].metric("Median", f"{stats['median']:.2f}" if isinstance(stats['median'], float) else stats['median'])
                                if "std" in stats:
                                    stat_cols[4].metric("Std Dev", f"{stats['std']:.2f}" if isinstance(stats['std'], float) else stats['std'])
                
                if cat_cols:
                    with st.expander("Categorical Column Statistics", expanded=True):
                        for col in cat_cols:
                            if col in summary["column_stats"]:
                                stats = summary["column_stats"][col]
                                st.markdown(f"#### {col}")
                                
                                # Display categorical stats
                                if "unique_count" in stats:
                                    st.metric("Unique Values", stats["unique_count"])
                                
                                # Display top values if available
                                if "top_values" in stats and stats["top_values"]:
                                    st.markdown("**Top Values:**")
                                    # Convert to DataFrame for better display
                                    top_values_df = pd.DataFrame({
                                        "Value": list(stats["top_values"].keys()),
                                        "Count": list(stats["top_values"].values())
                                    })
                                    st.dataframe(top_values_df)
        
        # Display data quality information with better formatting
        if "data_quality" in st.session_state.analysis:
            st.subheader("Data Quality")
            
            quality = st.session_state.analysis["data_quality"]
            
            # Improved missing values display
            if "missing_values" in quality:
                missing = quality["missing_values"]
                
                # Show missing value metrics
                missing_cols = st.columns(2)
                with missing_cols[0]:
                    st.metric("Total Missing Values", missing.get("total_missing", 0))
                with missing_cols[1]:
                    st.metric("Missing Percentage", f"{missing.get('missing_percentage', 0):.2f}%")
                
                # Show columns with missing values in a table
                if missing.get("columns_with_missing"):
                    st.markdown("**Columns with missing values:**")
                    missing_df = pd.DataFrame({
                        "Column": list(missing["columns_with_missing"].keys()),
                        "Missing Count": list(missing["columns_with_missing"].values())
                    })
                    st.dataframe(missing_df)
            
            # Improved duplicates display
            if "duplicates" in quality:
                duplicates = quality["duplicates"]
                
                duplicate_cols = st.columns(2)
                with duplicate_cols[0]:
                    st.metric("Duplicate Rows", duplicates.get("duplicate_rows", 0))
                with duplicate_cols[1]:
                    st.metric("Duplicate Percentage", f"{duplicates.get('duplicate_percentage', 0):.2f}%")
            
            # Improved outliers display
            if "outliers" in quality and quality["outliers"]:
                st.markdown("**Potential outliers detected:**")
                
                # Create a DataFrame of outliers for better display
                outlier_data = []
                for col, outlier_info in quality["outliers"].items():
                    outlier_data.append({
                        "Column": col,
                        "Outlier Count": outlier_info['outlier_count'],
                        "Percentage": f"{outlier_info['outlier_percentage']:.2f}%",
                        "Lower Bound": outlier_info['lower_bound'],
                        "Upper Bound": outlier_info['upper_bound']
                    })
                
                if outlier_data:
                    st.dataframe(pd.DataFrame(outlier_data))
        
        # Display visualizations with improved UI
        if "visualizations" in st.session_state.analysis:
            st.subheader("Recommended Visualizations")
            
            viz_list = st.session_state.analysis["visualizations"]
            
            if viz_list:
                # Create tabs for different visualizations
                viz_tabs = []
                for viz in viz_list[:5]:  # Limit to 5 visualizations
                    tab_name = f"{viz['title'].split('(')[0]}"
                    viz_tabs.append(tab_name)
                
                if viz_tabs:
                    viz_selected = st.radio("Select visualization:", viz_tabs, horizontal=True)
                    
                    # Get the selected visualization
                    selected_index = viz_tabs.index(viz_selected)
                    viz_config = viz_list[selected_index]
                    
                    # Create the visualization
                    if st.session_state.csv_data is not None:
                        fig = None
                        
                        if viz_config["type"] == "histogram":
                            fig = px.histogram(
                                st.session_state.csv_data,
                                x=viz_config["config"]["x"],
                                title=viz_config["title"],
                                template="plotly_white"
                            )
                        
                        elif viz_config["type"] == "bar":
                            fig = px.bar(
                                st.session_state.csv_data,
                                x=viz_config["config"]["x"],
                                y=viz_config["config"]["y"] if "y" in viz_config["config"] else None,
                                title=viz_config["title"],
                                template="plotly_white"
                            )
                        
                        elif viz_config["type"] == "line":
                            fig = px.line(
                                st.session_state.csv_data,
                                x=viz_config["config"]["x"],
                                y=viz_config["config"]["y"],
                                title=viz_config["title"],
                                template="plotly_white"
                            )
                        
                        elif viz_config["type"] == "scatter":
                            fig = px.scatter(
                                st.session_state.csv_data,
                                x=viz_config["config"]["x"],
                                y=viz_config["config"]["y"],
                                title=viz_config["title"],
                                template="plotly_white"
                            )
                        
                        elif viz_config["type"] == "box":
                            fig = px.box(
                                st.session_state.csv_data,
                                y=viz_config["config"]["y"] if "y" in viz_config["config"] else None,
                                x=viz_config["config"]["x"] if "x" in viz_config["config"] else None,
                                title=viz_config["title"],
                                template="plotly_white"
                            )
                        
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown(f"**Description:** {viz_config['description']}")
    else:
        st.info("Please upload a CSV file to see the automatic analysis.")

# Tab 3: Chat Interface
with tab3:
    st.header("Chat with your CSV")
    
    # Display conversation history with improved formatting
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            with st.chat_message("assistant"):
                # Format the explanation for better readability
                formatted_content = format_explanation(message["content"])
                st.markdown(formatted_content)
                
                # Extract and display KPIs if available
                if "result" in message:
                    kpis = extract_kpis(message["result"])
                    if kpis:
                        display_kpis(kpis)
                
                # Display visualization if available
                if "visualization" in message:
                    viz_type = message.get("visualization_type", "none")
                    viz_data = message.get("result")
                    
                    if viz_type != "none" and viz_data:
                        fig = create_visualization(viz_data, viz_type)
                        
                        if fig:
                            if isinstance(fig, str) and fig.startswith("data:image"):
                                # Display base64 encoded image
                                st.image(fig)
                            else:
                                # Display Plotly figure
                                st.plotly_chart(fig, use_container_width=True)
                
                # Display code if available in a cleaner way
                if "code" in message and message["code"]:
                    with st.expander("View Code"):
                        st.code(message["code"], language="python")
                
                # Display raw result in a cleaner way
                if "result" in message and message["result"]:
                    with st.expander("View Raw Result"):
                        if isinstance(message["result"], dict) and "type" in message["result"] and message["result"]["type"] == "dataframe":
                            # Convert dataframe to a nicer display
                            df = pd.DataFrame(message["result"]["data"])
                            st.dataframe(df)
                        else:
                            st.json(message["result"])
    
    # Input for new query with improved styling
    if st.session_state.file_id:
        prompt = st.chat_input("Ask a question about your data...")
        
        if prompt:
            # Display user message
            st.chat_message("user").write(prompt)
            
            # Add to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Process the query
            response = query_csv(
                file_id=st.session_state.file_id,
                query=prompt,
                conversation_id=st.session_state.conversation_id
            )
            
            # Save conversation ID
            if "conversation_id" in response:
                st.session_state.conversation_id = response["conversation_id"]
            
            # Create response message
            response_content = response.get("explanation", "")
            
            if "error" in response and response["error"]:
                response_content = f"Error: {response['error']}\n\n{response_content}"
            
            # Format the response content
            formatted_content = format_explanation(response_content)
            
            # Display assistant message with improved formatting
            with st.chat_message("assistant"):
                st.markdown(formatted_content)
                
                # Extract and display KPIs if available
                if "result" in response:
                    kpis = extract_kpis(response["result"])
                    if kpis:
                        display_kpis(kpis)
                
                # Display visualization if available
                viz_type = response.get("visualization_type", "none")
                viz_data = response.get("result")
                
                if viz_type != "none" and viz_data:
                    fig = create_visualization(viz_data, viz_type)
                    
                    if fig:
                        if isinstance(fig, str) and fig.startswith("data:image"):
                            # Display base64 encoded image
                            st.image(fig)
                        else:
                            # Display Plotly figure
                            st.plotly_chart(fig, use_container_width=True)
                
                # Display code if available
                if "code" in response and response["code"]:
                    with st.expander("View Code"):
                        st.code(response["code"], language="python")
                
                # Display raw result if available
                if "result" in response and response["result"]:
                    with st.expander("View Raw Result"):
                        if isinstance(response["result"], dict) and "type" in response["result"] and response["result"]["type"] == "dataframe":
                            # Convert dataframe to a nicer display
                            df = pd.DataFrame(response["result"]["data"])
                            st.dataframe(df)
                        else:
                            st.json(response["result"])
            
            # Add to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_content,
                "code": response.get("code"),
                "result": response.get("result"),
                "visualization_type": viz_type,
                "visualization": fig if 'fig' in locals() else None
            })
    else:
        st.info("Please upload a CSV file to start asking questions about your data.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888;'>CSV Conversation Agent - Powered by AI</p>", unsafe_allow_html=True)