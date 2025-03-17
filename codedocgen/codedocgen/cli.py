"""
Command-line interface for the Code Documentation Generator.
Provides commands for configuration and running the documentation generator.
"""

import os
import sys
import argparse
import logging
from typing import List, Optional, Dict, Any
import time
from pathlib import Path

os.environ["AUTOGEN_USE_DOCKER"] = "False"

from colorama import Fore, Style, init as colorama_init

from codedocgen.config import (
    get_config, 
    interactive_configuration, 
    print_current_config,
    get_config_file_path
)
from codedocgen.code_doc_generator import CodeDocumentationGenerator

# Initialize colorama for cross-platform colored terminal text
colorama_init()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("codedocgen.cli")


def show_banner() -> None:
    """Display the application banner."""
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║ {Fore.WHITE}CodeDocGen - Code Documentation Generator{Fore.CYAN}    ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Powered by AutoGen and Ollama{Style.RESET_ALL}\n")


def command_settings(args: argparse.Namespace) -> int:
    """
    Handle the 'settings' command to configure the application.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success)
    """
    show_banner()
    
    if args.show:
        print_current_config()
        return 0
    
    if args.reset:
        import os
        config_file = get_config_file_path()
        if os.path.exists(config_file):
            os.remove(config_file)
            print(f"{Fore.GREEN}Configuration reset to defaults.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No configuration file found to reset.{Style.RESET_ALL}")
        
        # Load the default config
        get_config()
        return 0
    
    # Interactive configuration
    interactive_configuration()
    return 0


def command_run(args: argparse.Namespace) -> int:
    """
    Handle the 'run' command to generate documentation.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    show_banner()
    
    # Get working directory
    directory = args.directory or os.getcwd()
    directory = os.path.abspath(directory)
    
    print(f"{Fore.WHITE}Generating documentation for: {Fore.GREEN}{directory}{Style.RESET_ALL}")
    
    # Load configuration
    config = get_config()
    
    # Override config with command line arguments if provided
    if args.model:
        config["model"] = args.model
    
    if args.port:
        config["port"] = args.port
        
    if args.format:
        config["output_format"] = args.format
        
    if args.max_size:
        config["max_file_size"] = args.max_size * 1024  # Convert KB to bytes
        
    if args.timeout:
        config["timeout"] = args.timeout
        
    if args.exclude:
        # Append to existing excludes
        for exclude in args.exclude:
            if os.path.isdir(os.path.join(directory, exclude)):
                if exclude not in config["exclude_dirs"]:
                    config["exclude_dirs"].append(exclude)
            else:
                if exclude not in config["exclude_files"]:
                    config["exclude_files"].append(exclude)
    
    if args.extensions:
        # Convert extensions to proper format
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]
        config["include_extensions"] = extensions
        
    if args.output:
        output_dir = os.path.abspath(args.output)
    else:
        # Use a subdirectory of the current directory
        output_dir = os.path.join(directory, "code_docs")
    
    # Configure Ollama base URL
    ollama_base_url = f"http://localhost:{config['port']}"
    
    try:
        # Initialize the generator
        # Update this part in command_run function in cli.py

# Get the API key based on provider
        api_key = ""
        if config.get("provider") == "openai":
            api_key = config.get("openai_api_key", "")
            if not api_key:
                print(f"{Fore.RED}OpenAI API key is not set. Please run 'codedocgen settings' to configure.{Style.RESET_ALL}")
                return 1

        # Initialize the generator
        generator = CodeDocumentationGenerator(
            directory=directory,
            model=config["model"],
            output_format=config["output_format"],
            excludes=config["exclude_dirs"] + config["exclude_files"],
            max_file_size=config["max_file_size"],
            include_extensions=config.get("include_extensions"),
            output_dir=output_dir,
            verbose=args.verbose,
            timeout=config["timeout"],
            ollama_base_url=ollama_base_url,
            provider=config.get("provider", "ollama"),
            api_key=api_key  # Pass the correct API key
        )
        
        # Run the documentation generation
        print(f"{Fore.YELLOW}Starting documentation generation...{Style.RESET_ALL}")
        start_time = time.time()
        
        result = generator.run()
        
        elapsed_time = time.time() - start_time
        
        # Output results
        if result["status"] == "completed":
            print(f"\n{Fore.GREEN}✅ Documentation generation completed in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
            print(f"{Fore.WHITE}📊 Processed {result['stats']['total_files_processed']} files{Style.RESET_ALL}")
            print(f"{Fore.WHITE}📁 Documentation saved to: {Fore.GREEN}{output_dir}{Style.RESET_ALL}")
            
            if result.get("index_file"):
                rel_index = os.path.relpath(result['index_file'], os.getcwd())
                print(f"{Fore.WHITE}📑 Index file: {Fore.GREEN}{rel_index}{Style.RESET_ALL}")
            
            if result["stats"].get("errors") and len(result["stats"]["errors"]) > 0:
                print(f"{Fore.YELLOW}⚠️ Encountered {len(result['stats']['errors'])} errors during processing{Style.RESET_ALL}")
                
            return 0
        else:
            print(f"\n{Fore.RED}❌ {result['message']}{Style.RESET_ALL}")
            return 1
            
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        return 1


def print_color(text: str, color: str) -> None:
    """
    Print text with specified color using colorama.
    
    Args:
        text: The text to print
        color: Color name ('red', 'green', 'yellow', etc.)
    """
    color_map = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE,
    }
    color_code = color_map.get(color.lower(), Fore.WHITE)
    print(f"{color_code}{text}{Style.RESET_ALL}")


def format_size(size_bytes: int) -> str:
    """Format file size in bytes to a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024


def command_generate(args):
    """Handle the generate command."""
    try:
        # Load configuration
        config = get_config()
        
        # Get the API key based on provider
        api_key = ""
        if config.get("provider") == "openai":
            api_key = config.get("openai_api_key", "")
            if not api_key:
                print(f"{Fore.RED}OpenAI API key is not set. Please run 'codedocgen settings' to configure.{Style.RESET_ALL}")
                return 1
        
        # Setup the documentation generator
        generator = CodeDocumentationGenerator(
            directory=args.directory,
            provider=config.get("provider", "ollama"),
            api_key=api_key,
            model=config.get("model", "mistral"),
            output_format=config.get("output_format", "markdown"),
            max_file_size=config.get("max_file_size", 500 * 1024),
            timeout=config.get("timeout", 60),
            verbose=args.verbose,
            output_dir=args.output,
            ollama_base_url=f"http://localhost:{config.get('port', 11434)}"
        )
        
        # Run the generation process
        results = generator.run()
        
        # Print results summary
        if results["status"] == "completed":
            print_color(results["message"], 'green')
            print(f"Documentation index: {results['index_file']}")
            print(f"Files processed: {results['stats']['total_files_processed']}")
            print(f"Files skipped: {results['stats']['total_files_skipped']}")
            print(f"Total code size: {format_size(results['stats']['total_bytes_processed'])}")
            
            if results['stats']['errors']:
                print_color(f"Errors encountered: {len(results['stats']['errors'])}", 'yellow')
                if args.verbose:
                    for error in results['stats']['errors']:
                        print_color(f"  - {error['file']}: {error['error']}", 'yellow')
            
            return 0
        else:
            print_color(results["message"], 'red')
            return 1
            
    except Exception as e:
        print_color(f"Error: {str(e)}", 'red')
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command line arguments (uses sys.argv if None)
        
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="CodeDocGen - Code Documentation Generator using AutoGen and Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  codedocgen run                    # Generate docs for current directory
  codedocgen run ~/projects/myapp   # Generate docs for specific directory
  codedocgen settings               # Configure settings interactively
  codedocgen settings --show        # Show current configuration
        """
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Settings command
    settings_parser = subparsers.add_parser("settings", help="Configure application settings")
    settings_parser.add_argument("--show", action="store_true", help="Show current settings")
    settings_parser.add_argument("--reset", action="store_true", help="Reset settings to defaults")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Generate documentation")
    run_parser.add_argument("directory", nargs="?", help="Directory to scan (default: current directory)")
    run_parser.add_argument("--model", help="Ollama model to use (overrides config)")
    run_parser.add_argument("--port", type=int, help="Ollama API port (overrides config)")
    run_parser.add_argument("--format", choices=["markdown", "html", "json"], 
                         help="Output format (overrides config)")
    run_parser.add_argument("--output", help="Output directory for documentation")
    run_parser.add_argument("--exclude", nargs="+", help="Directories or files to exclude")
    run_parser.add_argument("--max-size", type=int, 
                         help="Maximum file size in KB to process (overrides config)")
    run_parser.add_argument("--extensions", nargs="+", 
                         help="File extensions to include (e.g., py js ts)")
    run_parser.add_argument("--timeout", type=int,
                         help="Timeout for API calls in seconds (overrides config)")
    run_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Handle commands
    if parsed_args.command == "settings":
        return command_settings(parsed_args)
    elif parsed_args.command == "run":
        return command_run(parsed_args)
    elif parsed_args.command == "version":
        from codedocgen import __version__
        print(f"CodeDocGen version {__version__}")
        return 0
    else:
        # No command specified, show help
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
