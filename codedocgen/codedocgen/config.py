"""
Configuration management for the Code Documentation Generator.
Handles loading, saving, and interactive configuration with questionary.
"""

import os
import json
import logging
import questionary
from pathlib import Path
import yaml
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("codedocgen.config")

# Default configuration values
DEFAULT_CONFIG = {
    "provider": "ollama",  # 'ollama' or 'openai'
    "model": "mistral",
    "port": 11434,
    "openai_api_key": "",
    "output_format": "markdown",
    "max_file_size": 500 * 1024,  # 500KB
    "timeout": 60,
    "exclude_dirs": [
        ".git", ".github", "__pycache__", "node_modules", "venv", "env",
        "dist", "build", ".idea", ".vscode", ".pytest_cache"
    ],
    "exclude_files": [
        "package-lock.json", "yarn.lock", ".gitignore", ".DS_Store",
    ],
    "available_ollama_models": [
        "mistral", "llama2", "codellama", "phi", "gemma", "mixtral", "vicuna"
    ],
    "available_openai_models": [
        "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4-vision"
    ]
}

# Config file location
CONFIG_DIR = os.path.expanduser("~/.config/codedocgen")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from the config file.
    If the file doesn't exist, create it with default values.
    
    Returns:
        Dict containing configuration values
    """
    ensure_config_dir()
    
    if not os.path.exists(CONFIG_FILE):
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
            
        # Merge with defaults to ensure all keys exist
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                
        return config
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        logger.info("Using default configuration")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to the config file.
    
    Args:
        config: Dictionary containing configuration values
    """
    ensure_config_dir()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        logger.info(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Error saving config file: {e}")


def interactive_configuration(existing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Interactively configure the application using questionary.
    
    Args:
        existing_config: Optional existing configuration to modify
        
    Returns:
        Updated configuration dictionary
    """
    from colorama import Fore, Style, init
    init()  # Initialize colorama
    
    # Load existing config or use defaults
    config = existing_config or load_config()
    
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║ {Fore.WHITE}CodeDocGen Configuration{Fore.CYAN}                    ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Configure how the documentation generator works.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Press Enter to keep the current value.{Style.RESET_ALL}\n")
    
    # Model provider selection
    provider = questionary.select(
        "Which model provider would you like to use?",
        choices=["ollama", "openai"],
        default=config.get("provider", "ollama")
    ).ask()
    
    if provider:
        config["provider"] = provider
        
        # If provider changed, set a default model appropriate for the provider
        current_model = config.get("model", "")
        if provider == "ollama" and current_model not in config.get("available_ollama_models", []):
            config["model"] = DEFAULT_CONFIG["available_ollama_models"][0]
        elif provider == "openai" and current_model not in config.get("available_openai_models", []):
            config["model"] = DEFAULT_CONFIG["available_openai_models"][0]
    
    # Model selection based on provider
    if config["provider"] == "ollama":
        # Ollama Model Selection
        available_models = config.get("available_ollama_models", DEFAULT_CONFIG["available_ollama_models"])
        model = questionary.select(
            "Which Ollama model would you like to use?",
            choices=available_models,
            default=config.get("model", available_models[0])
        ).ask()
        
        if model:
            config["model"] = model
        
        # Custom model input
        use_custom_model = questionary.confirm(
            "Would you like to specify a different model not in the list?",
            default=False
        ).ask()
        
        if use_custom_model:
            custom_model = questionary.text(
                "Enter the name of the Ollama model:",
                default=config.get("model", available_models[0])
            ).ask()
            
            if custom_model:
                config["model"] = custom_model
                if custom_model not in config["available_ollama_models"]:
                    config["available_ollama_models"].append(custom_model)
        
        # Ollama API Port
        port_str = questionary.text(
            "Ollama API port:",
            default=str(config.get("port", 11434))
        ).ask()
        
        try:
            if port_str:
                config["port"] = int(port_str)
        except ValueError:
            print(f"{Fore.RED}Invalid port number. Using default: {config.get('port', 11434)}{Style.RESET_ALL}")
    
    else:  # OpenAI
        # OpenAI Model Selection
        available_models = config.get("available_openai_models", DEFAULT_CONFIG["available_openai_models"])
        model = questionary.select(
            "Which OpenAI model would you like to use?",
            choices=available_models,
            default=config.get("model", available_models[0])
        ).ask()
        
        if model:
            config["model"] = model
        
        # Custom model input
        use_custom_model = questionary.confirm(
            "Would you like to specify a different model not in the list?",
            default=False
        ).ask()
        
        if use_custom_model:
            custom_model = questionary.text(
                "Enter the name of the OpenAI model:",
                default=config.get("model", available_models[0])
            ).ask()
            
            if custom_model:
                config["model"] = custom_model
                if custom_model not in config["available_openai_models"]:
                    config["available_openai_models"].append(custom_model)
        
        # OpenAI API Key
        current_key = config.get("openai_api_key", "")
        masked_key = "********" + current_key[-4:] if current_key and len(current_key) > 4 else ""
        
        api_key = questionary.password(
            "OpenAI API Key (press Enter to keep existing key):",
            default="" if not masked_key else masked_key
        ).ask()
        
        if api_key and api_key != masked_key:
            config["openai_api_key"] = api_key
    
    # Output Format
    output_format = questionary.select(
        "Output documentation format:",
        choices=["markdown", "html", "json"],
        default=config.get("output_format", "markdown")
    ).ask()
    
    if output_format:
        config["output_format"] = output_format
    
    # Max File Size
    max_size_kb_str = questionary.text(
        "Maximum file size to process (KB):",
        default=str(config.get("max_file_size", 500 * 1024) // 1024)
    ).ask()
    
    try:
        if max_size_kb_str:
            config["max_file_size"] = int(max_size_kb_str) * 1024
    except ValueError:
        print(f"{Fore.RED}Invalid size. Using default: {config.get('max_file_size', 500 * 1024) // 1024}KB{Style.RESET_ALL}")
    
    # API Timeout
    timeout_str = questionary.text(
        "API timeout in seconds:",
        default=str(config.get("timeout", 60))
    ).ask()
    
    try:
        if timeout_str:
            config["timeout"] = int(timeout_str)
    except ValueError:
        print(f"{Fore.RED}Invalid timeout. Using default: {config.get('timeout', 60)}s{Style.RESET_ALL}")
    
    # Save the configuration
    save_config(config)
    
    print(f"\n{Fore.GREEN}✓ Configuration saved successfully!{Style.RESET_ALL}")
    return config


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    If the config file doesn't exist, create it with default values.
    
    Returns:
        Dict containing configuration values
    """
    return load_config()


def get_config_file_path() -> str:
    """
    Get the path to the configuration file.
    
    Returns:
        String path to the config file
    """
    return CONFIG_FILE


def print_current_config() -> None:
    """Print the current configuration values."""
    from colorama import Fore, Style, init
    init()  # Initialize colorama
    
    config = load_config()
    
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║ {Fore.WHITE}Current CodeDocGen Configuration{Fore.CYAN}             ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    print(f"{Fore.WHITE}Provider:{Style.RESET_ALL} {config.get('provider', 'ollama')}")
    print(f"{Fore.WHITE}Model:{Style.RESET_ALL} {config.get('model', 'mistral')}")
    
    if config.get('provider') == 'ollama':
        print(f"{Fore.WHITE}Ollama Port:{Style.RESET_ALL} {config.get('port', 11434)}")
    elif config.get('provider') == 'openai':
        api_key = config.get('openai_api_key', '')
        masked_key = "********" + api_key[-4:] if api_key and len(api_key) > 4 else "Not Set"
        print(f"{Fore.WHITE}OpenAI API Key:{Style.RESET_ALL} {masked_key}")
    
    print(f"{Fore.WHITE}Output Format:{Style.RESET_ALL} {config.get('output_format', 'markdown')}")
    print(f"{Fore.WHITE}Max File Size:{Style.RESET_ALL} {config.get('max_file_size', 500 * 1024) // 1024}KB")
    print(f"{Fore.WHITE}API Timeout:{Style.RESET_ALL} {config.get('timeout', 60)}s")
    print(f"{Fore.WHITE}Excluded Directories:{Style.RESET_ALL} {', '.join(config.get('exclude_dirs', []))}")
    print(f"{Fore.WHITE}Excluded Files:{Style.RESET_ALL} {', '.join(config.get('exclude_files', []))}")
    print(f"\n{Fore.WHITE}Config File Location:{Style.RESET_ALL} {CONFIG_FILE}")


if __name__ == "__main__":
    # Test configuration functionality
    interactive_configuration()
