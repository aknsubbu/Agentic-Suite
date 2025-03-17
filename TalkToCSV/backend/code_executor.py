# """Module for safely executing generated pandas code snippets."""

# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import io
# import base64
# import logging
# from typing import Dict, List, Any, Optional, Tuple
# import ast
# import sys
# from contextlib import redirect_stdout, redirect_stderr
# import traceback

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class CodeExecutor:
#     """Class for executing pandas code snippets safely."""
    
#     def __init__(self):
#         """Initialize the code executor."""
#         # Allowed modules for safe execution
#         self.allowed_modules = {
#             'pandas': pd,
#             'pd': pd,
#             'numpy': np,
#             'np': np,
#             'matplotlib.pyplot': plt,
#             'plt': plt
#         }
    
#     def execute_code(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
#         """Execute pandas code safely and return the results.
        
#         Args:
#             code: Python code to execute
#             df: DataFrame to operate on
            
#         Returns:
#             Dictionary with execution results or error message
#         """
#         # Capture stdout and stderr
#         stdout_buffer = io.StringIO()
#         stderr_buffer = io.StringIO()
        
#         try:
#             # Check if code contains unsafe operations
#             if not self._is_code_safe(code):
#                 return {
#                     "status": "error",
#                     "message": "Code contains unsafe operations",
#                     "output": None,
#                     "result": None
#                 }
            
#             # Remove import statements - we'll handle imports directly
#             modified_code = self._remove_imports(code)
            
#             # Create a limited globals dictionary with safe modules
#             globals_dict = {
#                 "__builtins__": {
#                     key: __builtins__[key] for key in [
#                         'abs', 'all', 'any', 'bool', 'dict', 'enumerate',
#                         'filter', 'float', 'format', 'frozenset', 'int',
#                         'isinstance', 'issubclass', 'len', 'list', 'map',
#                         'max', 'min', 'next', 'range', 'round', 'set',
#                         'slice', 'sorted', 'str', 'sum', 'tuple', 'zip',
#                         'print'  # Add print for better debugging
#                     ]
#                 }
#             }
            
#             # Add allowed modules directly to globals_dict
#             globals_dict.update(self.allowed_modules)
            
#             # Create locals dictionary with the DataFrame
#             locals_dict = {"df": df}
            
#             # Check if code uses 'return' statement
#             if "return " in modified_code:
#                 # Wrap code in a function to handle return statements
#                 function_code = f"def execute_function():\n"
#                 # Indent each line of the code
#                 for line in modified_code.split('\n'):
#                     function_code += f"    {line}\n"
                
#                 # Add function call
#                 function_code += "\nresult = execute_function()"
                
#                 with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
#                     exec(function_code, globals_dict, locals_dict)
                
#                 result = locals_dict.get("result")
#             else:
#                 # Execute the code directly
#                 with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
#                     exec(modified_code, globals_dict, locals_dict)
                
#                 # Try to get the result from a variable named 'result' first
#                 result = locals_dict.get("result")
                
#                 # If no 'result' variable, look for last assignment
#                 if result is None:
#                     # Check if the last line is an expression (like df.head())
#                     lines = modified_code.strip().split('\n')
#                     if lines and not any(op in lines[-1] for op in ['=', 'return', 'print']):
#                         # Last line is an expression, so evaluate it
#                         try:
#                             result_code = f"result = {lines[-1]}"
#                             with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
#                                 exec(result_code, globals_dict, locals_dict)
#                             result = locals_dict.get("result")
#                         except:
#                             pass
                
#                 # If still no result, try to find the last assignment
#                 if result is None:
#                     try:
#                         tree = ast.parse(modified_code)
#                         assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
                        
#                         if assignments:
#                             # Get the target of the last assignment
#                             last_assignment = assignments[-1]
#                             if isinstance(last_assignment.targets[0], ast.Name):
#                                 var_name = last_assignment.targets[0].id
#                                 if var_name in locals_dict:
#                                     result = locals_dict[var_name]
#                     except SyntaxError:
#                         # If there's a syntax error in parsing, just continue
#                         pass
            
#             # If still no result, return the DataFrame
#             if result is None:
#                 result = df
            
#             # Get stdout and stderr
#             stdout = stdout_buffer.getvalue()
#             stderr = stderr_buffer.getvalue()
            
#             # Process the result
#             processed_result = self._process_result(result)
            
#             return {
#                 "status": "success",
#                 "message": "Code executed successfully",
#                 "output": stdout if stdout else stderr,
#                 "result": processed_result
#             }
#         except Exception as e:
#             logger.error(f"Error executing code: {str(e)}")
#             # Get the full traceback
#             stderr = stderr_buffer.getvalue()
#             if not stderr:
#                 stderr = traceback.format_exc()
            
#             return {
#                 "status": "error",
#                 "message": f"Error executing code: {str(e)}",
#                 "output": stderr,
#                 "result": None
#             }
    
#     def _remove_imports(self, code: str) -> str:
#         """Remove import statements from code, as we're providing modules directly.
        
#         Args:
#             code: Python code
            
#         Returns:
#             Code with import statements removed
#         """
#         try:
#             tree = ast.parse(code)
#             lines = code.split('\n')
#             lines_to_remove = []
            
#             for node in ast.walk(tree):
#                 if isinstance(node, (ast.Import, ast.ImportFrom)):
#                     start_line = node.lineno - 1  # AST line numbers are 1-indexed
#                     lines_to_remove.append(start_line)
            
#             # Remove the import lines (in reverse order to not affect indices)
#             for line_no in sorted(lines_to_remove, reverse=True):
#                 lines.pop(line_no)
            
#             return '\n'.join(lines)
#         except SyntaxError:
#             # If there's a syntax error, just return the original code
#             return code
    
#     def _is_code_safe(self, code: str) -> bool:
#         """Check if code contains potentially unsafe operations.
        
#         Args:
#             code: Python code to check
            
#         Returns:
#             True if code is safe, False otherwise
#         """
#         # Check for imports we don't allow
#         try:
#             tree = ast.parse(code)
            
#             for node in ast.walk(tree):
#                 # Check Import nodes
#                 if isinstance(node, ast.Import):
#                     for name in node.names:
#                         module_name = name.name.split('.')[0]
#                         if module_name not in self.allowed_modules:
#                             return False
                
#                 # Check ImportFrom nodes
#                 elif isinstance(node, ast.ImportFrom):
#                     module_name = node.module.split('.')[0] if node.module else ''
#                     if module_name and module_name not in self.allowed_modules:
#                         return False
#         except SyntaxError:
#             # If there's a syntax error, be conservative and return False
#             return False
        
#         # Check for file operations
#         unsafe_patterns = [
#             "open(", "file(", "__import__", "eval(", "exec(",
#             "subprocess", "os.", "sys.", "shutil", "pathlib",
#             "request", "socket", "ftplib"
#         ]
        
#         for pattern in unsafe_patterns:
#             if pattern in code:
#                 return False
        
#         return True
    
#     def _extract_imports(self, code: str) -> List[str]:
#         """Extract imported modules from code.
        
#         Args:
#             code: Python code
            
#         Returns:
#             List of imported module names
#         """
#         try:
#             tree = ast.parse(code)
#             imports = []
            
#             for node in ast.walk(tree):
#                 # Regular imports: import X, import X.Y
#                 if isinstance(node, ast.Import):
#                     for name in node.names:
#                         imports.append(name.name.split('.')[0])
#                 # From imports: from X import Y
#                 elif isinstance(node, ast.ImportFrom):
#                     if node.module:
#                         imports.append(node.module.split('.')[0])
            
#             return imports
#         except SyntaxError:
#             # If there's a syntax error, be conservative and return a list with an unknown module
#             return ["unknown_module"]
    
#     def _process_result(self, result: Any) -> Dict[str, Any]:
#         """Process and convert the result to a JSON-serializable format.
        
#         Args:
#             result: Result from code execution
            
#         Returns:
#             Processed result in serializable format
#         """
#         if result is None:
#             return None
        
#         # Convert DataFrame to dict
#         if isinstance(result, pd.DataFrame):
#             # Check size to avoid too large responses
#             if len(result) > 100:
#                 preview = result.head(100).to_dict(orient='records')
#                 return {
#                     "type": "dataframe",
#                     "data": preview,
#                     "truncated": True,
#                     "total_rows": len(result),
#                     "columns": list(result.columns)
#                 }
#             else:
#                 return {
#                     "type": "dataframe",
#                     "data": result.to_dict(orient='records'),
#                     "truncated": False,
#                     "total_rows": len(result),
#                     "columns": list(result.columns)
#                 }
        
#         # Convert Series to dict
#         elif isinstance(result, pd.Series):
#             return {
#                 "type": "series",
#                 "name": result.name,
#                 "data": result.to_dict(),
#                 "index": [str(idx) for idx in result.index]
#             }
        
#         # Convert matplotlib figure to base64 encoded PNG
#         elif isinstance(result, plt.Figure) or (hasattr(plt, "gcf") and result == plt.gcf()):
#             # If result is the current figure or a figure object
#             try:
#                 buffer = io.BytesIO()
#                 plt.savefig(buffer, format='png', bbox_inches='tight')
#                 buffer.seek(0)
#                 image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
#                 plt.close(result)  # Close the figure to free memory
                
#                 return {
#                     "type": "figure",
#                     "format": "png",
#                     "data": image_base64
#                 }
#             except Exception as e:
#                 logger.error(f"Error converting figure to base64: {str(e)}")
#                 plt.close(result)  # Make sure to close the figure even if conversion fails
#                 return str(result)
        
#         # Handle numpy arrays
#         elif isinstance(result, np.ndarray):
#             if result.ndim == 1:
#                 return {
#                     "type": "array",
#                     "data": result.tolist()
#                 }
#             else:
#                 return {
#                     "type": "array",
#                     "data": result.tolist(),
#                     "shape": result.shape
#                 }
        
#         # Handle numpy scalar types
#         elif np.isscalar(result) and isinstance(result, (np.number, np.bool_)):
#             return float(result) if isinstance(result, np.floating) else int(result)
        
#         # Handle other basic types
#         elif isinstance(result, (int, float, str, bool, list, dict)):
#             return result
        
#         # Default: convert to string
#         else:
#             return str(result)

# # Create a singleton instance
# code_executor = CodeExecutor()

"""Module for safely executing generated pandas code snippets."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import logging
from typing import Dict, List, Any, Optional, Tuple
import ast
import sys
from contextlib import redirect_stdout, redirect_stderr
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeExecutor:
    """Class for executing pandas code snippets safely."""
    
    def __init__(self):
        """Initialize the code executor."""
        # Allowed modules for safe execution
        self.allowed_modules = {
            'pandas': pd,
            'pd': pd,
            'numpy': np,
            'np': np,
            'matplotlib.pyplot': plt,
            'plt': plt
        }
    
    def execute_code(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute pandas code safely and return the results.
        
        Args:
            code: Python code to execute
            df: DataFrame to operate on
            
        Returns:
            Dictionary with execution results or error message
        """
        # Log the code being executed
        logger.info(f"Executing code:\n{code}")
        
        # Capture stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        try:
            # Check if code contains unsafe operations
            if not self._is_code_safe(code):
                return {
                    "status": "error",
                    "message": "Code contains unsafe operations",
                    "output": None,
                    "result": None
                }
            
            # Remove import statements - we'll handle imports directly
            modified_code = self._remove_imports(code)
            
            # Create a dictionary for the execution environment
            # This is a crucial part - we need to add all modules and the DataFrame here
            exec_globals = {
                'pd': pd,
                'pandas': pd,
                'np': np,
                'numpy': np,
                'plt': plt,
                'matplotlib.pyplot': plt,
                'df': df.copy(),  # Make a copy to avoid modifying the original
                '__builtins__': __builtins__  # This is important - without it basic functions won't work
            }
            
            # Execute the code
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(modified_code, exec_globals)
            
            # Try to get the result from a variable named 'result' first
            result = exec_globals.get("result")
            
            # If no 'result' variable, look for the last expression
            if result is None:
                # Try some common variable names
                for var_name in ['output', 'summary', 'analysis', 'stats', 'df_result', 'data']:
                    if var_name in exec_globals and var_name != 'df' and not callable(exec_globals[var_name]):
                        result = exec_globals[var_name]
                        break
                
                # If still no result, return the DataFrame itself
                if result is None:
                    result = df.head()
            
            # Get stdout and stderr
            stdout = stdout_buffer.getvalue()
            stderr = stderr_buffer.getvalue()
            
            # Process the result
            processed_result = self._process_result(result)
            
            return {
                "status": "success",
                "message": "Code executed successfully",
                "output": stdout if stdout else stderr,
                "result": processed_result
            }
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            # Get the full traceback
            stderr = stderr_buffer.getvalue()
            if not stderr:
                stderr = traceback.format_exc()
            
            # In case of error, return the DataFrame as a fallback
            try:
                return {
                    "status": "error",
                    "message": f"Error executing code: {str(e)}",
                    "output": stderr,
                    "result": self._process_result(df.head())
                }
            except Exception:
                return {
                    "status": "error",
                    "message": f"Error executing code: {str(e)}",
                    "output": stderr,
                    "result": None
                }
    
    def _remove_imports(self, code: str) -> str:
        """Remove import statements from code, as we're providing modules directly.
        
        Args:
            code: Python code
            
        Returns:
            Code with import statements removed
        """
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            lines_to_remove = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    start_line = node.lineno - 1  # AST line numbers are 1-indexed
                    lines_to_remove.append(start_line)
            
            # Remove the import lines (in reverse order to not affect indices)
            for line_no in sorted(lines_to_remove, reverse=True):
                lines.pop(line_no)
            
            return '\n'.join(lines)
        except SyntaxError:
            # If there's a syntax error, just return the original code
            return code
    
    def _is_code_safe(self, code: str) -> bool:
        """Check if code contains potentially unsafe operations.
        
        Args:
            code: Python code to check
            
        Returns:
            True if code is safe, False otherwise
        """
        # Check for imports we don't allow
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Check Import nodes
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_name = name.name.split('.')[0]
                        if module_name not in self.allowed_modules:
                            return False
                
                # Check ImportFrom nodes
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name not in self.allowed_modules:
                            return False
        except SyntaxError:
            # If there's a syntax error, be conservative and return False
            return False
        
        # Check for file operations
        unsafe_patterns = [
            "open(", "file(", "__import__", "eval(", "exec(",
            "subprocess", "os.", "sys.", "shutil", "pathlib",
            "request", "socket", "ftplib"
        ]
        
        for pattern in unsafe_patterns:
            if pattern in code:
                return False
        
        return True
    
    def _process_result(self, result: Any) -> Dict[str, Any]:
        """Process and convert the result to a JSON-serializable format.
        
        Args:
            result: Result from code execution
            
        Returns:
            Processed result in serializable format
        """
        if result is None:
            return None
        
        # Convert DataFrame to dict
        if isinstance(result, pd.DataFrame):
            # Check size to avoid too large responses
            if len(result) > 100:
                preview = result.head(100).to_dict(orient='records')
                return {
                    "type": "dataframe",
                    "data": preview,
                    "truncated": True,
                    "total_rows": len(result),
                    "columns": list(result.columns)
                }
            else:
                return {
                    "type": "dataframe",
                    "data": result.to_dict(orient='records'),
                    "truncated": False,
                    "total_rows": len(result),
                    "columns": list(result.columns)
                }
        
        # Convert Series to dict
        elif isinstance(result, pd.Series):
            return {
                "type": "series",
                "name": result.name,
                "data": result.to_dict(),
                "index": [str(idx) for idx in result.index]
            }
        
        # Convert matplotlib figure to base64 encoded PNG
        elif isinstance(result, plt.Figure) or (hasattr(plt, "gcf") and result == plt.gcf()):
            # If result is the current figure or a figure object
            try:
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close(result)  # Close the figure to free memory
                
                return {
                    "type": "figure",
                    "format": "png",
                    "data": image_base64
                }
            except Exception as e:
                logger.error(f"Error converting figure to base64: {str(e)}")
                plt.close(result)  # Make sure to close the figure even if conversion fails
                return str(result)
        
        # Handle numpy arrays
        elif isinstance(result, np.ndarray):
            if result.ndim == 1:
                return {
                    "type": "array",
                    "data": result.tolist()
                }
            else:
                return {
                    "type": "array",
                    "data": result.tolist(),
                    "shape": result.shape
                }
        
        # Handle numpy scalar types
        elif np.isscalar(result) and isinstance(result, (np.number, np.bool_)):
            return float(result) if isinstance(result, np.floating) else int(result)
        
        # Handle other basic types
        elif isinstance(result, (int, float, str, bool, list, dict)):
            return result
        
        # Default: convert to string
        else:
            return str(result)

# Create a singleton instance
code_executor = CodeExecutor()