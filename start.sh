#!/bin/bash

# AI Document Summarization Platform - Startup Script

echo "=================================="
echo "AI Document Platform Startup"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download models
echo "Downloading required models..."
python scripts/init_models.py

# Create directories
echo "Creating necessary directories..."
mkdir -p uploads processed logs static templates

# Initialize database
echo "Initializing database..."
python -c "from app.models.database import init_db; init_db()"

# Start server
echo "Starting server..."
echo "=================================="
echo "Server will be available at:"
echo "  http://localhost:8000"
echo "  API Docs: http://localhost:8000/api/docs"
echo "=================================="

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
