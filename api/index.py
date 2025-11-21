"""
Vercel serverless function entry point for FastAPI backend
"""
import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app

# This is the entry point that Vercel will use
# Vercel expects a variable called 'app' or a function called 'handler'
handler = app
