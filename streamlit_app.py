"""
Main Streamlit App Entry Point

This file serves as the entry point for the Streamlit application.
It properly sets up the path and runs the main app from the frontend directory.
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add frontend directory to path for local imports
frontend_dir = os.path.join(current_dir, "frontend")
sys.path.insert(0, frontend_dir)

# Execute the frontend Streamlit app code
try:
    exec(open(os.path.join(frontend_dir, "streamlit_app.py")).read())
except Exception as e:
    import streamlit as st

    st.error(f"❌ Failed to load the application: {e}")
    st.subheader("🔧 Setup Instructions")
    st.info("1. Ensure you're running from the project root directory")
    st.info("2. Install all dependencies: `pip install -r requirements.txt`")
    st.info("3. Check that the frontend directory structure is intact")
    st.info("4. Start the FastAPI backend server on port 8000")
    st.stop()
