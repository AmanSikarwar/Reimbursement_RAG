#!/bin/bash

# Quick Start Script for Invoice Reimbursement System Frontend
# This script helps users quickly start the Streamlit frontend

echo "🚀 Starting Invoice Reimbursement System Frontend..."

# Check if we're in the right directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: streamlit_app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Using existing virtual environment..."
    source venv/bin/activate
else
    echo "📦 No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated."
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Check if Streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "❌ Error: Streamlit is not installed. Installing now..."
    pip install streamlit
fi

# Check backend status
echo "🔍 Checking backend status..."
if curl -s http://localhost:8000/api/v1/health/quick > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "⚠️  Backend is not running on port 8000"
    echo "📝 To start the backend, run: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi

# Start Streamlit
echo "🌟 Starting Streamlit frontend on http://localhost:8501..."
echo "📝 Press Ctrl+C to stop the server"
echo ""

# Run Streamlit
python -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
