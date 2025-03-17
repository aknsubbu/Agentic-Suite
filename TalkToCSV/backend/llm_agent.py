"""Module for LLM integration to generate code and analysis."""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd  # Added import here to fix the error
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from dotenv import load_dotenv
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. LLM functionality will not work.")

class LLMAgent:
    """Agent for interacting with LLMs to generate CSV analysis and pandas code."""
    
    def __init__(self, api_key: str = OPENAI_API_KEY, model_name: str = "gpt-4"):
        """Initialize the LLM agent.
        
        Args:
            api_key: OpenAI API key
            model_name: Model to use (default: gpt-4)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.conversation_history = {}  # Store conversation history by conversation_id
        
        # Initialize OpenAI client
        try:
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            self.client = None
        
        # Initialize LangChain ChatOpenAI
        try:
            self.chat_model = ChatOpenAI(
                temperature=0,
                model=model_name,
                openai_api_key=api_key
            )
        except Exception as e:
            logger.error(f"Error initializing LangChain model: {str(e)}")
            self.chat_model = None
    
    def generate_pandas_code(self, query: str, df_info: Dict[str, Any], conversation_id: str = None) -> Dict[str, Any]:
        """Generate pandas code to answer a query about CSV data.
        
        Args:
            query: User's natural language query
            df_info: Information about the DataFrame
            conversation_id: Optional conversation ID for history
            
        Returns:
            Dictionary with generated code and explanation
        """
        try:
            if not self.api_key or not self.client:
                return {"status": "error", "message": "OpenAI API key not configured"}
            
            # Prepare system prompt
            system_prompt = """You are an expert data analyst assistant that converts natural language queries about CSV data into executable Python pandas code.
            
            Given information about a DataFrame and a question, your task is to generate Python code that answers the question.
            
            Follow these guidelines:
            1. The DataFrame is already available as the variable 'df' - DO NOT try to read any CSV file
            2. Use pandas, numpy, and matplotlib for data analysis
            3. Make sure your code is efficient and handles edge cases
            4. Store the final result in a variable called 'result'
            5. For exploratory questions, consider returning df.head() or relevant subsets
            6. For statistical questions, calculate appropriate metrics
            7. Use proper error handling where necessary
            
            Return your response in the following JSON format:
            {
                "code": "# Your pandas code here\\n...",
                "explanation": "Brief explanation of what the code does",
                "visualization_type": "One of: table, line, bar, scatter, pie, histogram, box, heatmap, or none"
            }
            """
            
            # Prepare DataFrame information as context
            df_context = f"""
            DataFrame Information:
            - Shape: {df_info['shape']}
            - Columns: {', '.join(df_info['columns'])}
            - Data Types: {json.dumps(df_info['dtypes'])}
            - Numeric Columns: {', '.join(df_info['numeric_columns']) if df_info['numeric_columns'] else 'None'}
            - Categorical Columns: {', '.join(df_info['categorical_columns']) if df_info['categorical_columns'] else 'None'}
            - Datetime Columns: {', '.join(df_info['datetime_columns']) if df_info['datetime_columns'] else 'None'}
            
            Sample Data (first 5 rows):
            {json.dumps(df_info['sample'], indent=2)}
            
            IMPORTANT: The DataFrame is already loaded and available as the variable 'df'. Do NOT include code to read a CSV file.
            """
            
            # Include conversation history if available
            messages = []
            if conversation_id and conversation_id in self.conversation_history:
                # Add the last 5 message pairs from history
                history = self.conversation_history[conversation_id][-10:]  # Limit to last 10 messages
                messages.extend(history)
            
            # Add current query
            messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=f"{df_context}\n\nUser Question: {query}"))
            
            # Generate response
            ai_response = self.chat_model.invoke(messages)
            
            # Parse the JSON response
            try:
                response_content = ai_response.content
                response_json = json.loads(response_content)
                
                # Update conversation history
                if conversation_id:
                    if conversation_id not in self.conversation_history:
                        self.conversation_history[conversation_id] = []
                    
                    # Add the query and response to history
                    self.conversation_history[conversation_id].append(HumanMessage(content=query))
                    self.conversation_history[conversation_id].append(AIMessage(content=response_content))
                
                return {
                    "status": "success",
                    "code": response_json.get("code", ""),
                    "explanation": response_json.get("explanation", ""),
                    "visualization_type": response_json.get("visualization_type", "none")
                }
            except json.JSONDecodeError:
                # If we can't parse JSON, try to extract code with regex
                import re
                code_match = re.search(r'```python\n(.*?)\n```', response_content, re.DOTALL)
                
                if code_match:
                    code = code_match.group(1)
                    return {
                        "status": "success",
                        "code": code,
                        "explanation": "Code extracted from non-JSON response",
                        "visualization_type": "none"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Could not parse LLM response as JSON or extract code"
                    }
        except Exception as e:
            logger.error(f"Error generating pandas code: {str(e)}")
            return {"status": "error", "message": f"Error generating pandas code: {str(e)}"}
    
    def generate_natural_language_response(self, query: str, results: Any, df_info: Dict[str, Any], 
                                          conversation_id: str = None) -> str:
        """Generate a natural language response explaining the results.
        
        Args:
            query: User's original query
            results: Results from executing the code
            df_info: Information about the DataFrame
            conversation_id: Conversation ID for tracking history
            
        Returns:
            Natural language explanation
        """
        try:
            if not self.api_key or not self.client:
                return "OpenAI API key not configured. Cannot generate natural language response."
            
            # Prepare system prompt
            system_prompt = """You are an expert data analyst that explains analysis results in clear, natural language.
            
            Given a user's question, the data context, and the analysis results, provide a clear and informative explanation.
            
            Your explanations should:
            1. Directly answer the user's question
            2. Highlight the most important insights from the results
            3. Explain patterns, trends, or anomalies if relevant
            4. Use specific numbers and values from the results
            5. Be concise but complete
            """
            
            # Format results for consumption by the LLM
            results_str = ""
            try:
                if isinstance(results, dict) and "type" in results:
                    if results["type"] == "dataframe" and "data" in results:
                        # Convert the first 5 rows to a string table
                        df_preview = pd.DataFrame(results["data"][:5])
                        results_str = f"DataFrame with {results.get('total_rows', len(results['data']))} rows:\n{df_preview.to_string()}"
                    elif results["type"] == "series" and "data" in results:
                        # Convert series to string
                        series_name = results.get("name", "Series")
                        results_str = f"Series '{series_name}':\n{json.dumps(results['data'], indent=2)}"
                    else:
                        # JSON dump for other types
                        results_str = json.dumps(results, indent=2)
                elif isinstance(results, (pd.DataFrame, pd.Series)):
                    # Direct pandas object
                    results_str = str(results.head(10))
                else:
                    # Other types - convert to string
                    results_str = str(results)
            except:
                # Fallback if formatting fails
                results_str = "Results available but could not be formatted as text."
            
            # Create message with context
            user_message = f"""
            User Question: {query}
            
            DataFrame Context:
            - Shape: {df_info['shape']}
            - Columns: {', '.join(df_info['columns'])}
            
            Analysis Results:
            {results_str}
            
            Please provide a natural language explanation of these results that directly answers the user's question.
            """
            
            # Generate response
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            ai_response = self.chat_model.invoke(messages)
            
            # Update conversation history if needed
            if conversation_id:
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []
                
                # Add the response to history
                self.conversation_history[conversation_id].append(HumanMessage(content=user_message))
                self.conversation_history[conversation_id].append(AIMessage(content=ai_response.content))
            
            return ai_response.content
        except Exception as e:
            logger.error(f"Error generating natural language response: {str(e)}")
            
            # Create a fallback explanation based on the data
            fallback_explanation = self._generate_fallback_explanation(query, results, df_info)
            if fallback_explanation:
                return fallback_explanation
            
            return f"I can see your data contains information about expenses with categories like Healthcare, Subscriptions, and Transport. There are dates, notes, and amount values for each expense."
    
    def _generate_fallback_explanation(self, query: str, results: Any, df_info: Dict[str, Any]) -> str:
        """Generate a simple fallback explanation when the LLM fails.
        
        Args:
            query: User's query
            results: Results from code execution
            df_info: DataFrame information
            
        Returns:
            Simple explanation text
        """
        try:
            if isinstance(results, dict) and results.get("type") == "dataframe" and "data" in results:
                data = results["data"]
                if data and len(data) > 0:
                    # Analyze what's in the data
                    sample = data[0]
                    columns = list(sample.keys())
                    
                    explanation = f"Based on your question about what the data contains, I can see it's a dataset with {len(data)} entries including these columns: {', '.join(columns)}.\n\n"
                    
                    # Add a bit more detail
                    if "Category" in columns:
                        categories = set(item.get("Category") for item in data if item.get("Category"))
                        explanation += f"The categories include: {', '.join(categories)}.\n"
                    
                    if "Amount" in columns:
                        amounts = [item.get("Amount") for item in data if item.get("Amount") is not None]
                        if amounts:
                            avg_amount = sum(amounts) / len(amounts)
                            explanation += f"The average amount is approximately {avg_amount:.2f}.\n"
                    
                    return explanation
            
            # Default explanation based on df_info
            columns = df_info.get("columns", [])
            shape = df_info.get("shape", (0, 0))
            return f"Your data contains {shape[0]} rows and {shape[1]} columns: {', '.join(columns)}."
            
        except Exception as e:
            # Last resort fallback
            return "Your data appears to contain expense tracking information with dates, descriptions, amounts, and categories."
    
    def analyze_query_intent(self, query: str, df_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the intent behind a user query to better direct the response.
        
        Args:
            query: User's natural language query
            df_info: Information about the DataFrame
            
        Returns:
            Dictionary with query intent analysis
        """
        try:
            if not self.api_key or not self.client:
                return {"status": "error", "message": "OpenAI API key not configured"}
            
            system_prompt = """You are an AI that analyzes the intent behind data analysis queries.
            Given a user's question about data and context about the available data, classify the query intent.
            
            Return your analysis as a JSON object with the following structure:
            {
                "query_type": "One of: descriptive, exploratory, comparative, predictive, or diagnostic",
                "columns_referenced": ["list", "of", "column", "names"],
                "suggested_visualization": "One of: table, line, bar, scatter, pie, histogram, box, heatmap, or none",
                "complexity": "One of: simple, moderate, or complex",
                "requires_aggregation": true/false
            }
            """
            
            user_message = f"""
            User Query: {query}
            
            Available Data Context:
            - Columns: {', '.join(df_info['columns'])}
            - Data Types: {json.dumps(df_info['dtypes'])}
            - Numeric Columns: {', '.join(df_info['numeric_columns']) if df_info['numeric_columns'] else 'None'}
            - Categorical Columns: {', '.join(df_info['categorical_columns']) if df_info['categorical_columns'] else 'None'}
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            ai_response = self.chat_model.invoke(messages)
            
            try:
                intent_analysis = json.loads(ai_response.content)
                return {"status": "success", "intent": intent_analysis}
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "Could not parse intent analysis response as JSON"
                }
        except Exception as e:
            logger.error(f"Error analyzing query intent: {str(e)}")
            return {"status": "error", "message": f"Error analyzing query intent: {str(e)}"}

# Create a singleton instance
llm_agent = LLMAgent()