# """Main FastAPI application for CSV Conversation Agent."""

# from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel, Field
# from typing import Dict, List, Any, Optional
# import logging
# import os
# import json
# import base64
# import uuid
# from datetime import datetime

# # Import application modules
# from csv_processor import csv_processor
# from llm_agent import llm_agent
# from code_executor import code_executor

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Create FastAPI app
# app = FastAPI(
#     title="CSV Conversation Agent API",
#     description="API for conversational analysis of CSV files",
#     version="0.1.0"
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )

# # Pydantic models for request/response
# class ChunkUploadRequest(BaseModel):
#     """Request model for uploading a chunk of a CSV file."""
#     file_id: Optional[str] = None
#     chunk_number: int
#     total_chunks: Optional[int] = None
#     data: str  # Base64 encoded chunk
#     is_last: bool
#     filename: str

# class QueryRequest(BaseModel):
#     """Request model for querying a CSV file."""
#     file_id: str
#     query: str
#     conversation_id: Optional[str] = None

# class QueryResponse(BaseModel):
#     """Response model for query results."""
#     query_id: str
#     conversation_id: str
#     query: str
#     code: Optional[str] = None
#     result: Any = None
#     explanation: Optional[str] = None
#     error: Optional[str] = None
#     visualization_type: Optional[str] = None

# # In-memory storage for query results
# query_results = {}

# @app.get("/")
# async def root():
#     """Root endpoint for API health check."""
#     return {"status": "ok", "message": "CSV Conversation Agent API is running"}

# @app.post("/upload/chunk")
# async def upload_chunk(chunk: ChunkUploadRequest):
#     """Upload a chunk of a CSV file.
    
#     For large files, the frontend splits the file into chunks and uploads them sequentially.
#     The backend reassembles the chunks once all are received.
#     """
#     try:
#         # If file_id is not provided, generate a new one for the first chunk
#         file_id = chunk.file_id if chunk.file_id else str(uuid.uuid4())
        
#         # Process the chunk
#         result = csv_processor.process_chunk(
#             file_id=file_id,
#             chunk_number=chunk.chunk_number,
#             data=chunk.data,
#             is_last=chunk.is_last
#         )
        
#         # If this is the first chunk, return the file_id
#         if not chunk.file_id:
#             result["file_id"] = file_id
        
#         return result
#     except Exception as e:
#         logger.error(f"Error processing chunk: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error processing chunk: {str(e)}")

# @app.post("/upload/file")
# async def upload_file(file: UploadFile = File(...)):
#     """Upload a small CSV file in a single request.
    
#     This endpoint is for smaller files that don't need chunking.
#     """
#     try:
#         # Read the file
#         contents = await file.read()
        
#         # Generate a file ID
#         file_id = str(uuid.uuid4())
        
#         # Save the file
#         file_path = os.path.join(csv_processor.UPLOAD_DIR, f"{file_id}.csv")
#         with open(file_path, "wb") as f:
#             f.write(contents)
        
#         # Process the file
#         result = csv_processor.process_csv(file_path, file_id)
        
#         return result
#     except Exception as e:
#         logger.error(f"Error uploading file: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# @app.get("/files/{file_id}")
# async def get_file_info(file_id: str):
#     """Get information about a previously uploaded file."""
#     try:
#         # Get the DataFrame info
#         df_info = csv_processor.get_dataframe_info(file_id)
        
#         if "status" in df_info and df_info["status"] == "error":
#             raise HTTPException(status_code=404, detail=df_info["message"])
        
#         return df_info
#     except Exception as e:
#         logger.error(f"Error getting file info: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")

# @app.get("/files/{file_id}/analysis")
# async def get_file_analysis(file_id: str):
#     """Get comprehensive analysis of a CSV file."""
#     try:
#         # Generate analysis
#         analysis = csv_processor.generate_analysis(file_id)
        
#         if "status" in analysis and analysis["status"] == "error":
#             raise HTTPException(status_code=404, detail=analysis["message"])
        
#         return analysis
#     except Exception as e:
#         logger.error(f"Error generating analysis: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error generating analysis: {str(e)}")

# @app.post("/query", response_model=QueryResponse)
# async def query_csv(request: QueryRequest):
#     """Process a natural language query on a CSV file."""
#     try:
#         # Get the DataFrame
#         df = csv_processor.get_dataframe(request.file_id)
#         if df is None:
#             raise HTTPException(status_code=404, detail="File not found")
        
#         # Get DataFrame info for context
#         df_info = csv_processor.get_dataframe_info(request.file_id)
        
#         # Generate conversation ID if not provided
#         conversation_id = request.conversation_id or str(uuid.uuid4())
        
#         # Generate query ID
#         query_id = str(uuid.uuid4())
        
#         # Analyze query intent
#         # intent = llm_agent.analyze_query_intent(request.query, df_info)
        
#         # Generate pandas code
#         code_result = llm_agent.generate_pandas_code(
#             query=request.query,
#             df_info=df_info,
#             conversation_id=conversation_id
#         )
        
#         if code_result["status"] == "error":
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "query_id": query_id,
#                     "conversation_id": conversation_id,
#                     "query": request.query,
#                     "error": code_result["message"]
#                 }
#             )
        
#         # Execute the generated code
#         execution_result = code_executor.execute_code(
#             code=code_result["code"],
#             df=df
#         )
        
#         if execution_result["status"] == "error":
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "query_id": query_id,
#                     "conversation_id": conversation_id,
#                     "query": request.query,
#                     "code": code_result["code"],
#                     "error": execution_result["message"],
#                     "output": execution_result["output"]
#                 }
#             )
        
#         # Generate natural language explanation
#         explanation = llm_agent.generate_natural_language_response(
#             query=request.query,
#             results=execution_result["result"],
#             df_info=df_info,
#             conversation_id=conversation_id
#         )
        
#         # Store the result for later retrieval
#         query_results[query_id] = {
#             "query_id": query_id,
#             "conversation_id": conversation_id,
#             "query": request.query,
#             "code": code_result["code"],
#             "result": execution_result["result"],
#             "explanation": explanation,
#             "visualization_type": code_result["visualization_type"],
#             "timestamp": datetime.now().isoformat()
#         }
        
#         # Return the response
#         return {
#             "query_id": query_id,
#             "conversation_id": conversation_id,
#             "query": request.query,
#             "code": code_result["code"],
#             "result": execution_result["result"],
#             "explanation": explanation,
#             "visualization_type": code_result["visualization_type"]
#         }
#     except Exception as e:
#         logger.error(f"Error processing query: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# @app.get("/query/{query_id}")
# async def get_query_result(query_id: str):
#     """Get the result of a previously executed query."""
#     if query_id not in query_results:
#         raise HTTPException(status_code=404, detail="Query result not found")
    
#     return query_results[query_id]

# @app.get("/conversations/{conversation_id}")
# async def get_conversation_history(conversation_id: str):
#     """Get the history of a conversation."""
#     try:
#         # Check if conversation exists
#         if conversation_id not in llm_agent.conversation_history:
#             return {"conversation_id": conversation_id, "messages": []}
        
#         # Convert LangChain messages to simple format
#         messages = []
#         for msg in llm_agent.conversation_history[conversation_id]:
#             if hasattr(msg, 'type') and msg.type == 'human':
#                 messages.append({"role": "user", "content": msg.content})
#             elif hasattr(msg, 'type') and msg.type == 'ai':
#                 messages.append({"role": "assistant", "content": msg.content})
        
#         return {"conversation_id": conversation_id, "messages": messages}
#     except Exception as e:
#         logger.error(f"Error getting conversation history: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


"""Main FastAPI application for CSV Conversation Agent."""

from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
import os
import json
import base64
import uuid
from datetime import datetime

# Import application modules
from csv_processor import csv_processor
from llm_agent import llm_agent
from code_executor import code_executor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CSV Conversation Agent API",
    description="API for conversational analysis of CSV files",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic models for request/response
class ChunkUploadRequest(BaseModel):
    """Request model for uploading a chunk of a CSV file."""
    file_id: Optional[str] = None
    chunk_number: int
    total_chunks: Optional[int] = None
    data: str  # Base64 encoded chunk
    is_last: bool
    filename: str

class QueryRequest(BaseModel):
    """Request model for querying a CSV file."""
    file_id: str
    query: str
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for query results."""
    query_id: str
    conversation_id: str
    query: str
    code: Optional[str] = None
    result: Any = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    visualization_type: Optional[str] = None

# In-memory storage for query results
query_results = {}

@app.get("/")
async def root():
    """Root endpoint for API health check."""
    return {"status": "ok", "message": "CSV Conversation Agent API is running"}

@app.post("/upload/chunk")
async def upload_chunk(chunk: ChunkUploadRequest):
    """Upload a chunk of a CSV file.
    
    For large files, the frontend splits the file into chunks and uploads them sequentially.
    The backend reassembles the chunks once all are received.
    """
    try:
        # If file_id is not provided, generate a new one for the first chunk
        file_id = chunk.file_id if chunk.file_id else str(uuid.uuid4())
        
        # Process the chunk
        result = csv_processor.process_chunk(
            file_id=file_id,
            chunk_number=chunk.chunk_number,
            data=chunk.data,
            is_last=chunk.is_last
        )
        
        # If this is the first chunk, return the file_id
        if not chunk.file_id:
            result["file_id"] = file_id
        
        return result
    except Exception as e:
        logger.error(f"Error processing chunk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chunk: {str(e)}")

@app.post("/upload/file")
async def upload_file(file: UploadFile = File(...)):
    """Upload a small CSV file in a single request.
    
    This endpoint is for smaller files that don't need chunking.
    """
    try:
        # Read the file
        contents = await file.read()
        
        # Generate a file ID
        file_id = str(uuid.uuid4())
        
        # Save the file
        file_path = os.path.join(csv_processor.UPLOAD_DIR, f"{file_id}.csv")
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Process the file
        result = csv_processor.process_csv(file_path, file_id)
        
        return result
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get information about a previously uploaded file."""
    try:
        # Get the DataFrame info
        df_info = csv_processor.get_dataframe_info(file_id)
        
        if "status" in df_info and df_info["status"] == "error":
            raise HTTPException(status_code=404, detail=df_info["message"])
        
        return df_info
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")

@app.get("/files/{file_id}/analysis")
async def get_file_analysis(file_id: str):
    """Get comprehensive analysis of a CSV file."""
    try:
        # Generate analysis
        analysis = csv_processor.generate_analysis(file_id)
        
        if "status" in analysis and analysis["status"] == "error":
            raise HTTPException(status_code=404, detail=analysis["message"])
        
        return analysis
    except Exception as e:
        logger.error(f"Error generating analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating analysis: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_csv(request: QueryRequest):
    """Process a natural language query on a CSV file."""
    try:
        # Get the DataFrame
        df = csv_processor.get_dataframe(request.file_id)
        if df is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get DataFrame info for context
        df_info = csv_processor.get_dataframe_info(request.file_id)
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Generate query ID
        query_id = str(uuid.uuid4())
        
        # Log incoming query
        logger.info(f"Received query: '{request.query}'")
        
        # Generate pandas code using LLM
        code_result = llm_agent.generate_pandas_code(
            query=request.query,
            df_info=df_info,
            conversation_id=conversation_id
        )
        
        if "status" in code_result and code_result["status"] == "error":
            logger.error(f"Error in code generation: {code_result['message']}")
            # Simple fallback for code generation errors
            simple_code = """
            # Simple data overview
            result = df.head(10)
            """
            code_result = {
                "code": simple_code,
                "explanation": "Displaying the first few rows of data",
                "visualization_type": "table"
            }
        
        # Execute the generated code
        execution_result = code_executor.execute_code(
            code=code_result["code"],
            df=df
        )
        
        if execution_result["status"] == "error":
            logger.error(f"Code execution error: {execution_result['message']}")
            logger.error(f"Code that failed: {code_result['code']}")
            
            # We'll continue with the error but still provide some data
            # The code_executor has been updated to return df.head() in case of errors
        
        # Generate natural language explanation
        logger.info("Generating natural language explanation")
        explanation = llm_agent.generate_natural_language_response(
            query=request.query,
            results=execution_result["result"],
            df_info=df_info,
            conversation_id=conversation_id
        )
        
        # Store the result for later retrieval
        query_results[query_id] = {
            "query_id": query_id,
            "conversation_id": conversation_id,
            "query": request.query,
            "code": code_result["code"],
            "result": execution_result["result"],
            "explanation": explanation,
            "visualization_type": code_result.get("visualization_type", "none"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Return the response
        return {
            "query_id": query_id,
            "conversation_id": conversation_id,
            "query": request.query,
            "code": code_result["code"],
            "result": execution_result["result"],
            "explanation": explanation,
            "visualization_type": code_result.get("visualization_type", "none")
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/query/{query_id}")
async def get_query_result(query_id: str):
    """Get the result of a previously executed query."""
    if query_id not in query_results:
        raise HTTPException(status_code=404, detail="Query result not found")
    
    return query_results[query_id]

@app.get("/conversations/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get the history of a conversation."""
    try:
        # Check if conversation exists
        if conversation_id not in llm_agent.conversation_history:
            return {"conversation_id": conversation_id, "messages": []}
        
        # Convert LangChain messages to simple format
        messages = []
        for msg in llm_agent.conversation_history[conversation_id]:
            if hasattr(msg, 'type') and msg.type == 'human':
                messages.append({"role": "user", "content": msg.content})
            elif hasattr(msg, 'type') and msg.type == 'ai':
                messages.append({"role": "assistant", "content": msg.content})
        
        return {"conversation_id": conversation_id, "messages": messages}
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)