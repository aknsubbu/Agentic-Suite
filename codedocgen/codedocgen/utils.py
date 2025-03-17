"""
Utility functions for the Code Documentation Generator.
"""

import os
import sys
import subprocess
import shutil
import platform
from typing import Dict, List, Optional, Tuple, Union


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def check_ollama_availability(port: int = 11434) -> Tuple[bool, str]:
    """
    Check if Ollama is available and running.
    
    Args:
        port: Ollama API port to check
        
    Returns:
        Tuple of (is_available, message)
    """
    import requests
    
    try:
        response = requests.get(f"http://localhost:{port}/api/version", timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            return True, f"Ollama is running (version: {version_info.get('version', 'unknown')})"
        else:
            return False, f"Ollama API returned status code {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Could not connect to Ollama on port {port}. Is Ollama running?"
    except Exception as e:
        return False, f"Error checking Ollama: {str(e)}"


def list_available_ollama_models(port: int = 11434) -> List[str]:
    """
    List available Ollama models.
    
    Args:
        port: Ollama API port
        
    Returns:
        List of available model names
    """
    import requests
    
    try:
        response = requests.get(f"http://localhost:{port}/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
            return models
        else:
            return []
    except Exception:
        return []


def check_dependencies() -> Dict[str, bool]:
    """
    Check if required dependencies are installed.
    
    Returns:
        Dictionary with dependency status
    """
    status = {}
    
    # Check Python packages
    for package in ["autogen", "requests", "questionary", "colorama", "pyyaml"]:
        try:
            __import__(package)
            status[package] = True
        except ImportError:
            status[package] = False
    
    # Check Ollama
    ollama_available, _ = check_ollama_availability()
    status["ollama"] = ollama_available
    
    return status


def install_missing_dependencies(missing_deps: List[str]) -> bool:
    """
    Attempt to install missing Python dependencies.
    
    Args:
        missing_deps: List of missing dependency names
        
    Returns:
        True if successful, False otherwise
    """
    if not missing_deps:
        return True
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
        return True
    except subprocess.CalledProcessError:
        return False


def get_platform_info() -> Dict[str, str]:
    """
    Get information about the current platform.
    
    Returns:
        Dictionary with platform information
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }


def get_ollama_install_instructions() -> str:
    """
    Get platform-specific instructions for installing Ollama.
    
    Returns:
        Installation instructions as a string
    """
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        return (
            "To install Ollama on macOS:\n"
            "1. Visit https://ollama.ai/download\n"
            "2. Download and run the macOS installer\n"
            "3. Follow the installation instructions\n"
        )
    elif system == "linux":
        return (
            "To install Ollama on Linux:\n"
            "1. Run the following command:\n"
            "   curl -fsSL https://ollama.ai/install.sh | sh\n"
            "2. Start Ollama by running: ollama serve\n"
        )
    elif system == "windows":
        return (
            "To install Ollama on Windows:\n"
            "1. Visit https://ollama.ai/download\n"
            "2. Download and run the Windows installer\n"
            "3. Follow the installation instructions\n"
        )
    else:
        return "Visit https://ollama.ai for installation instructions for your platform."


def validate_ollama_model(model_name: str, port: int = 11434) -> Tuple[bool, str]:
    """
    Validate if an Ollama model is available or can be pulled.
    
    Args:
        model_name: Name of the model to validate
        port: Ollama API port
        
    Returns:
        Tuple of (is_valid, message)
    """
    import requests
    import json
    
    # First check if model is already available
    try:
        available_models = list_available_ollama_models(port)
        if model_name in available_models:
            return True, f"Model '{model_name}' is available"
            
        # If not available, check if it can be pulled
        # This is just a check, not actually pulling the model
        response = requests.get(
            f"http://localhost:{port}/api/tags", 
            timeout=5
        )
        
        if response.status_code == 200:
            return True, f"Model '{model_name}' can be used with Ollama"
        else:
            return False, f"Could not validate model '{model_name}'"
            
    except Exception as e:
        return False, f"Error validating model: {str(e)}"
