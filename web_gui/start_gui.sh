#!/bin/bash

echo "======================================"
echo "Starting MCP Server Web GUI"
echo "======================================"
echo ""

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/Updating dependencies..."
pip install -q -r requirements.txt

echo ""
echo "======================================"
echo "Starting Flask server..."
echo "======================================"
echo ""
echo "Access the GUI at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
