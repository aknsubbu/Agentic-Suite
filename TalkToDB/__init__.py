"""
TalkToDB - A database agent system for natural language interaction with databases.

This package provides tools for exploring databases, executing queries, and visualizing results
using a multi-agent AI system based on OpenAI models.
"""

__version__ = '0.1.0'
__author__ = 'Anandkumar NS'

# Import key classes to make them available at the package level
from .dbInterface import DatabaseExplorer
from .mongoConnect import MongoDBClient