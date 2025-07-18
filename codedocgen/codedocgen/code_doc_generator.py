"""
Code Documentation Generator using AutoGen and Ollama

This module contains the main CodeDocumentationGenerator class that:
1. Scans a directory for code files
2. Uses Ollama LLM to analyze each file
3. Generates documentation with proper formatting
4. Handles errors and edge cases gracefully
"""

import os
import sys
import time
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union, Any
import mimetypes
import importlib.util

from codedocgen.utils import format_size

try:
    import autogen
    from autogen import AssistantAgent
except ImportError:
    print("Error: Required packages not installed.")
    print("Please install the required packages using:")
    print("pip install ag2 requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("code_documentation.log")
    ]
)
logger = logging.getLogger("CodeDocGen")

# File type patterns
CODE_FILE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'React JSX',
    '.tsx': 'React TSX',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.cs': 'C#',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.rs': 'Rust',
    '.sh': 'Shell Script',
    '.pl': 'Perl',
    '.pm': 'Perl Module',
    '.scala': 'Scala',
    '.lua': 'Lua',
    '.r': 'R',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.tf': 'Terraform',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.md': 'Markdown',
    '.rst': 'reStructuredText',
}

# Directories to exclude from scanning
DEFAULT_EXCLUDE_DIRS = {
    '.git', '.github', '__pycache__', 'node_modules', 'venv', 'env',
    'dist', 'build', '.idea', '.vscode', '.pytest_cache', 'bin',
    'obj', 'target', '.output', '.next', '.nuxt'
}

# Files to exclude from scanning
DEFAULT_EXCLUDE_FILES = {
    'package-lock.json', 'yarn.lock', '.gitignore', '.DS_Store',
    'Thumbs.db', '.env', '.env.local', '.env.development',
    '.env.test', '.env.production'
}

class CodeDocumentationGenerator:
    """Main class for generating code documentation using AutoGen and Ollama."""
    
    def __init__(
        self, 
        directory: str,
        model: str = "llama3:8b",
        output_format: str = "markdown",
        excludes: Optional[List[str]] = None,
        max_file_size: int = 500 * 1024,  # 500KB max file size by default
        include_extensions: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        verbose: bool = False,
        timeout: int = 60,
        config_file: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434",
        provider: str = "ollama",
        api_key: str = "",
    ):
        """
        Initialize the documentation generator.
        
        Args:
            directory: Root directory to scan for code files
            model: Model to use (default depends on provider)
            output_format: Documentation format (markdown/html/json)
            excludes: List of directories or files to exclude
            max_file_size: Maximum file size to process in bytes
            include_extensions: List of file extensions to include (overrides defaults)
            output_dir: Directory to save documentation output
            verbose: Enable verbose output
            timeout: Timeout for API calls in seconds
            config_file: Path to JSON configuration file
            ollama_base_url: Base URL for Ollama API (only used with ollama provider)
            provider: Model provider ('ollama' or 'openai')
            api_key: API key for OpenAI (required if provider is 'openai')
        """
        self.directory = os.path.abspath(directory)
        self.model = model
        self.output_format = output_format
        self.max_file_size = max_file_size
        self.verbose = verbose
        self.timeout = timeout
        self.ollama_base_url = ollama_base_url
        self.provider = provider
        self.api_key = api_key
        
        # Validate provider setting
        if self.provider not in ["ollama", "openai"]:
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'ollama' or 'openai'")
            
        # Validate API key when using OpenAI
        if self.provider == "openai" and not self.api_key:
            logger.warning("No API key provided for OpenAI. You'll need to set this before generating documentation.")
        
        # Load config file if provided
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Update configuration from file
                    for key, value in config.items():
                        if hasattr(self, key) and value is not None:
                            setattr(self, key, value)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
        
        # Setup exclude patterns
        self.exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
        self.exclude_files = DEFAULT_EXCLUDE_FILES.copy()
        if excludes:
            for exclude in excludes:
                if os.path.isdir(os.path.join(directory, exclude)):
                    self.exclude_dirs.add(exclude)
                else:
                    self.exclude_files.add(exclude)
        
        # Setup file extensions to include
        if include_extensions:
            self.extensions = {ext if ext.startswith('.') else f'.{ext}': 
                            CODE_FILE_EXTENSIONS.get(ext if ext.startswith('.') else f'.{ext}', 'Unknown') 
                            for ext in include_extensions}
        else:
            self.extensions = CODE_FILE_EXTENSIONS
            
        # Output directory setup
        if output_dir:
            self.output_dir = os.path.abspath(output_dir)
            os.makedirs(self.output_dir, exist_ok=True)
        else:
            self.output_dir = os.path.join(self.directory, "code_docs")
            os.makedirs(self.output_dir, exist_ok=True)
            
        # Initialize stats
        self.stats = {
            "total_files_processed": 0,
            "total_files_skipped": 0,
            "total_bytes_processed": 0,
            "language_counts": {},
            "errors": [],
            "start_time": time.time(),
            "end_time": None,
            "duration": None
        }
        
        # Setup AutoGen agents
        self._setup_agents()
        
        logger.info(f"Initialized CodeDocumentationGenerator for directory: {self.directory}")
        logger.info(f"Using provider: {self.provider}")
        logger.info(f"Using model: {self.model}")
        logger.info(f"Output format: {self.output_format}")
        logger.info(f"Output directory: {self.output_dir}")

    def scan_directory(self) -> List[str]:
        """
        Scan the directory recursively and return a list of code files to process.
        
        Returns:
            List of file paths to be processed
        """
        code_files = []
        skipped_files = []
        
        try:
            for root, dirs, files in os.walk(self.directory):
                # Modify dirs in-place to exclude directories
                dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith('.')]
                
                # Process files in this directory
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.directory)
                    
                    # Skip excluded files
                    if file in self.exclude_files or any(rel_path.startswith(d) for d in self.exclude_dirs):
                        if self.verbose:
                            logger.debug(f"Skipping excluded file: {rel_path}")
                        continue
                    
                    # Check file extension
                    _, ext = os.path.splitext(file)
                    if ext.lower() not in self.extensions:
                        if self.verbose:
                            logger.debug(f"Skipping non-code file: {rel_path}")
                        continue
                    
                    # Check file size
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > self.max_file_size:
                            logger.warning(f"Skipping file exceeding max size ({file_size} bytes): {rel_path}")
                            skipped_files.append({"file": rel_path, "reason": "size_limit", "size": file_size})
                            self.stats["total_files_skipped"] += 1
                            continue
                    except Exception as e:
                        logger.error(f"Error checking file size for {rel_path}: {e}")
                        skipped_files.append({"file": rel_path, "reason": "error", "error": str(e)})
                        self.stats["total_files_skipped"] += 1
                        continue
                    
                    # File is valid, add to list
                    code_files.append(file_path)
                    
                    # Update language stats
                    lang = self.extensions.get(ext.lower(), "Unknown")
                    self.stats["language_counts"][lang] = self.stats["language_counts"].get(lang, 0) + 1
        
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            raise
        
        logger.info(f"Found {len(code_files)} code files to process")
        if skipped_files:
            logger.info(f"Skipped {len(skipped_files)} files")
        
        return code_files

    def _setup_agents(self):
        """Setup AutoGen agents with Ollama or OpenAI integration."""
        try:
            # Create the correct configuration based on provider
            if self.provider == "ollama":
                llm_config = {
                    "config_list": [
                        {
                            "model": self.model,
                            "api_type": "ollama",
                            "client_host": self.ollama_base_url,
                            "stream": False,
                            "temperature": 0.7,
                        }
                    ]
                }
                logger.info(f"Using Ollama with model: {self.model}")
            elif self.provider == "openai":
                # Check if API key is available for OpenAI
                if not self.api_key:
                    raise ValueError("OpenAI API key is required when using OpenAI provider")
                    
                llm_config = {
                    "config_list": [
                        {
                            "model": self.model,
                            "api_key": self.api_key,
                            "stream": False,
                            "temperature": 0.7,
                        }
                    ]
                }
                logger.info(f"Using OpenAI with model: {self.model}")
            else:
                raise ValueError(f"Unsupported provider: {self.provider}. Use 'ollama' or 'openai'.")
            
            # Create an Assistant Agent with the configured LLM
            self.ollama_agent = autogen.AssistantAgent(
                name="code_documentation_agent",
                llm_config=llm_config,
                system_message="""
                You are an expert code documentation assistant. Your task is to:
                1. Analyze code files and understand their structure
                2. Generate comprehensive documentation explaining:
                - Overall purpose of the file
                - Key functions, classes, and methods
                - Important dependencies and logic flow
                - Usage examples where appropriate
                3. Format documentation clearly and professionally
                4. Focus on accuracy and clarity in your documentation
                
                When documenting code, always include:
                - File purpose overview
                - Class and function descriptions
                - Parameter explanations
                - Return value descriptions
                - Example usage where helpful
                """
            )
            
            # Create a user proxy agent for managing interactions - DISABLE DOCKER
            self.user_proxy = autogen.UserProxyAgent(
                name="user_proxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                # Disable Docker for code execution
                code_execution_config={"use_docker": False}
            )
            
            logger.info("AutoGen agents successfully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize AutoGen agents: {e}")
            raise RuntimeError(f"Agent initialization failed: {e}")

    def generate_documentation_for_file(self, file_path: str) -> Dict[str, Any]:
        """
        Generate documentation for a single code file.
        
        Args:
            file_path: Path to the code file
            
        Returns:
            Dictionary containing documentation information
        """
        rel_path = os.path.relpath(file_path, self.directory)
        logger.info(f"Processing file: {rel_path}")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                code_content = f.read()
            
            file_size = len(code_content.encode('utf-8'))
            self.stats["total_bytes_processed"] += file_size
            
            # Get file extension and language
            _, ext = os.path.splitext(file_path)
            language = self.extensions.get(ext.lower(), "Unknown")
            
            # Create documentation prompt
            documentation_prompt = f"""
            Please generate documentation for the following {language} code file:
            File: {rel_path}
            
            ```{language.lower()}
            {code_content}
            ```
            
            Generate comprehensive documentation including:
            1. High-level overview of the file's purpose
            2. Main components (classes, functions, etc.) with descriptions
            3. Key algorithms or important logic explained
            4. Dependencies and relationships with other components
            5. Usage examples if appropriate
            
            Format the output as {self.output_format.upper()}.
            """
            
            # Use Assistant Agent to generate documentation through chat
            self.user_proxy.initiate_chat(
                self.ollama_agent,
                message=documentation_prompt
            )
            
            # Extract the response from the last message in the conversation
            response = self.ollama_agent.last_message()["content"]
            
            # Process and format the response
            documentation = self._format_documentation(
                response,
                file_path=rel_path,
                language=language
            )
            
            self.stats["total_files_processed"] += 1
            
            return {
                "file_path": rel_path,
                "language": language,
                "size_bytes": file_size,
                "documentation": documentation
            }
            
        except Exception as e:
            logger.error(f"Error generating documentation for {rel_path}: {e}")
            self.stats["errors"].append({
                "file": rel_path,
                "error": str(e),
                "type": type(e).__name__
            })
            return {
                "file_path": rel_path,
                "error": str(e),
                "documentation": f"# Documentation Generation Failed\n\nError: {str(e)}"
            }

    def _format_documentation(self, raw_doc: str, file_path: str, language: str) -> str:
        """
        Format the raw documentation based on the specified output format.
        
        Args:
            raw_doc: Raw documentation text from Ollama
            file_path: Path to the source file
            language: Programming language of the source file
            
        Returns:
            Formatted documentation string
        """
        # Extract the actual documentation content, removing any markdown code blocks if present
        content = raw_doc
        
        # Check if output already has the right format
        if self.output_format.lower() == "markdown":
            # Ensure proper markdown formatting
            if not content.startswith("# "):
                content = f"# Documentation: {file_path}\n\n{content}"
                
            # Add file info
            content = f"{content}\n\n---\n**File**: `{file_path}`  \n**Language**: {language}  \n**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                
        elif self.output_format.lower() == "html":
            # Convert markdown to HTML if needed
            try:
                import markdown
                html_content = markdown.markdown(content)
                
                content = f"""<!DOCTYPE html>
                <html>
                <head>
                    <title>Documentation: {file_path}</title>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; color: #333; }}
                        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                        code {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }}
                        h1, h2, h3 {{ color: #222; }}
                        .file-info {{ font-size: 0.9em; color: #555; border-top: 1px solid #eee; margin-top: 30px; padding-top: 10px; }}
                    </style>
                </head>
                <body>
                    <h1>Documentation: {os.path.basename(file_path)}</h1>
                    {html_content}
                    <div class="file-info">
                        <p><strong>File:</strong> {file_path}<br>
                        <strong>Language:</strong> {language}<br>
                        <strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </body>
                </html>
                """
            except ImportError:
                logger.warning("markdown package not found, outputting raw content")
                content = f"<h1>Documentation: {file_path}</h1>\n<pre>{content}</pre>"
                
        elif self.output_format.lower() == "json":
            # Format as JSON
            doc_data = {
                "file_path": file_path,
                "language": language,
                "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "content": content
            }
            
            try:
                content = json.dumps(doc_data, indent=2)
            except Exception as e:
                logger.error(f"Error formatting JSON: {e}")
                content = json.dumps({
                    "file_path": file_path,
                    "language": language,
                    "error": str(e),
                    "raw_content": str(content)
                })
                
        return content

    def save_documentation(self, doc_data: Dict[str, Any]) -> str:
        """
        Save the documentation to a file.
        
        Args:
            doc_data: Documentation data dictionary
            
        Returns:
            Path to the saved file
        """
        file_path = doc_data["file_path"]
        content = doc_data.get("documentation", "# Documentation generation failed")
        
        # Create directory structure mirroring the original
        rel_dir = os.path.dirname(file_path)
        output_path = os.path.join(self.output_dir, rel_dir)
        os.makedirs(output_path, exist_ok=True)
        
        # Determine output file name and extension
        base_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        
        if self.output_format.lower() == "markdown":
            output_file = f"{name_without_ext}.md"
        elif self.output_format.lower() == "html":
            output_file = f"{name_without_ext}.html"
        elif self.output_format.lower() == "json":
            output_file = f"{name_without_ext}.json"
        else:
            output_file = f"{name_without_ext}.txt"
            
        output_path = os.path.join(output_path, output_file)
        
        # Write the documentation to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Documentation saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving documentation: {e}")
            self.stats["errors"].append({
                "file": file_path,
                "error": str(e),
                "type": "save_error"
            })
            return None

    def generate_index(self) -> str:
        """
        Generate an index file that links to all documentation files.
        
        Returns:
            Path to the index file
        """
        logger.info("Generating documentation index")
        
        # Complete the stats
        self.stats["end_time"] = time.time()
        self.stats["duration"] = self.stats["end_time"] - self.stats["start_time"]
        
        # Format based on output type
        if self.output_format.lower() == "markdown":
            content = "# Code Documentation Index\n\n"
            content += f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Add statistics
            content += "## Statistics\n\n"
            content += f"- Total files processed: {self.stats['total_files_processed']}\n"
            content += f"- Total files skipped: {self.stats['total_files_skipped']}\n"
            content += f"- Total code size: {format_size(self.stats['total_bytes_processed'])}\n"
            content += f"- Processing time: {self.stats['duration']:.2f} seconds\n\n"
            
            # Add language breakdown
            content += "## Language Breakdown\n\n"
            for lang, count in self.stats["language_counts"].items():
                content += f"- {lang}: {count} files\n"
            
            content += "\n## Documentation Files\n\n"
            
            # Walk through the output directory and add links
            doc_files = []
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    if file != "index.md" and file.endswith(f".{self.output_format.lower()}"):
                        rel_path = os.path.relpath(os.path.join(root, file), self.output_dir)
                        doc_files.append(rel_path)
            
            # Sort files
            doc_files.sort()
            
            # Add links
            for doc_file in doc_files:
                file_name = os.path.basename(doc_file)
                dir_name = os.path.dirname(doc_file)
                if dir_name:
                    content += f"- [{file_name}](./{doc_file}) (in {dir_name})\n"
                else:
                    content += f"- [{file_name}](./{doc_file})\n"
            
            # Add error summary if any
            if self.stats["errors"]:
                content += "\n## Errors\n\n"
                for error in self.stats["errors"]:
                    content += f"- {error['file']}: {error['error']}\n"
            
            index_path = os.path.join(self.output_dir, "index.md")
            
        elif self.output_format.lower() == "html":
            # Create HTML index
            doc_files = []
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    if file != "index.html" and file.endswith(".html"):
                        rel_path = os.path.relpath(os.path.join(root, file), self.output_dir)
                        doc_files.append(rel_path)
            
            # Sort files
            doc_files.sort()
            
            # Build file list HTML
            file_list = ""
            for doc_file in doc_files:
                file_name = os.path.basename(doc_file)
                dir_name = os.path.dirname(doc_file)
                if dir_name:
                    file_list += f'<li><a href="./{doc_file}">{file_name}</a> <small>(in {dir_name})</small></li>\n'
                else:
                    file_list += f'<li><a href="./{doc_file}">{file_name}</a></li>\n'
            
            # Build language stats HTML
            lang_stats = ""
            for lang, count in self.stats["language_counts"].items():
                lang_stats += f'<li>{lang}: {count} files</li>\n'
            
            # Build error list HTML
            error_list = ""
            if self.stats["errors"]:
                for error in self.stats["errors"]:
                    error_list += f'<li>{error["file"]}: {error["error"]}</li>\n'
            
            content = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Code Documentation Index</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; color: #333; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    code {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }}
                    h1, h2, h3 {{ color: #222; }}
                    .stats {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }}
                    .stat-box {{ background: #f5f5f5; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px; }}
                    .file-list {{ list-style-type: none; padding-left: 0; }}
                    .file-list li {{ padding: 5px 0; border-bottom: 1px solid #eee; }}
                    .file-list li:last-child {{ border-bottom: none; }}
                    .error-list {{ color: #c00; }}
                </style>
            </head>
            <body>
                <h1>Code Documentation Index</h1>
                <p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>Statistics</h2>
                <div class="stats">
                    <div class="stat-box">
                        <h3>Files</h3>
                        <p>Processed: {self.stats['total_files_processed']}<br>
                        Skipped: {self.stats['total_files_skipped']}</p>
                    </div>
                    <div class="stat-box">
                        <h3>Code Size</h3>
                        <p>{format_size(self.stats['total_bytes_processed'])}</p>
                    </div>
                    <div class="stat-box">
                        <h3>Processing Time</h3>
                        <p>{self.stats['duration']:.2f} seconds</p>
                    </div>
                </div>
                
                <h2>Language Breakdown</h2>
                <ul>
                    {lang_stats}
                </ul>
                
                <h2>Documentation Files</h2>
                <ul class="file-list">
                    {file_list}
                </ul>
                
                {'<h2>Errors</h2><ul class="error-list">' + error_list + '</ul>' if error_list else ''}
            </body>
            </html>
            """
            
            index_path = os.path.join(self.output_dir, "index.html")
            
        elif self.output_format.lower() == "json":
            # Create JSON index
            doc_files = []
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    if file != "index.json" and file.endswith(".json"):
                        rel_path = os.path.relpath(os.path.join(root, file), self.output_dir)
                        doc_files.append(rel_path)
            
            # Sort files
            doc_files.sort()
            
            # Create index data
            index_data = {
                "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "stats": {
                    "total_files_processed": self.stats["total_files_processed"],
                    "total_files_skipped": self.stats["total_files_skipped"],
                    "total_bytes_processed": self.stats["total_bytes_processed"],
                    "processing_time_seconds": self.stats["duration"],
                    "language_counts": self.stats["language_counts"]
                },
                "documentation_files": doc_files,
                "errors": self.stats["errors"] if self.stats["errors"] else []
            }
            
            content = json.dumps(index_data, indent=2)
            index_path = os.path.join(self.output_dir, "index.json")
        
        # Write the index file
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Index file saved to: {index_path}")
            return index_path
        except Exception as e:
            logger.error(f"Error saving index file: {e}")
            return None

    def run(self):
        """
        Run the documentation generation process.
        
        Returns:
            Dictionary with results and statistics
        """
        logger.info(f"Starting documentation generation for {self.directory}")
        start_time = time.time()
        
        try:
            # Scan directory for code files
            code_files = self.scan_directory()
            
            if not code_files:
                logger.warning("No code files found to process")
                return {
                    "status": "completed",
                    "message": "No code files found to process",
                    "stats": self.stats
                }
            
            # Process each file
            total_files = len(code_files)
            for i, file_path in enumerate(code_files):
                rel_path = os.path.relpath(file_path, self.directory)
                logger.info(f"Processing file {i+1}/{total_files}: {rel_path}")
                
                try:
                    # Generate documentation
                    doc_data = self.generate_documentation_for_file(file_path)
                    
                    # Save documentation
                    self.save_documentation(doc_data)
                    
                except Exception as e:
                    logger.error(f"Failed to process {rel_path}: {e}")
                    self.stats["errors"].append({
                        "file": rel_path,
                        "error": str(e),
                        "type": "process_error"
                    })
            
            # Generate index file
            index_path = self.generate_index()
            
            # Complete and return results
            self.stats["end_time"] = time.time()
            self.stats["duration"] = self.stats["end_time"] - self.stats["start_time"]
            
            return {
                "status": "completed",
                "message": f"Documentation generation completed in {self.stats['duration']:.2f} seconds",
                "index_file": index_path,
                "stats": self.stats
            }
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return {
                "status": "failed",
                "message": f"Documentation generation failed: {e}",
                "stats": self.stats
            }
