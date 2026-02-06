#!/bin/bash
# Backend server startup script

echo "🚀 Starting Sovereign Scan Backend Server..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if port 8000 is in use
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Killing existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start the server
echo "🌐 Starting uvicorn server on port 8000..."
echo ""
uvicorn main:app --reload --port 8000 --log-level info
