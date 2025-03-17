#!/usr/bin/env python3
"""
Launcher script for the Database Agent Streamlit interface.
"""

import os
import argparse
from dotenv import load_dotenv

import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Launch the Database Agent Streamlit interface')
    parser.add_argument('--port', type=int, default=8501, help='Port to run Streamlit on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Set up CSS file if needed
    if not os.path.exists("style.css"):
        print("Creating CSS file...")
        from app import create_css_file
        create_css_file()
    
    # Build the Streamlit command
    command = f"streamlit run app.py --server.port {args.port}"
    
    if args.debug:
        command += " --logger.level=debug"
    
    # Run Streamlit
    print(f"Starting Streamlit server on port {args.port}...")
    os.system(command)

if __name__ == "__main__":
    main()