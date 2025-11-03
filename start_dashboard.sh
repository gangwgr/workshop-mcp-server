#!/bin/bash

# 🚀 Start Workshop MCP Server Dashboard with Proxy Support
# This script starts the Flask web dashboard for the MCP server

echo "🌐 Starting Workshop MCP Server Dashboard with Proxy..."

# Set proxy environment variables if not already set
if [ -z "$HTTP_PROXY" ]; then
    export HTTP_PROXY=http://proxy.redhat.com:8080
    echo "🔗 Set HTTP_PROXY=$HTTP_PROXY"
fi

if [ -z "$HTTPS_PROXY" ]; then
    export HTTPS_PROXY=http://proxy.redhat.com:8080  
    echo "🔗 Set HTTPS_PROXY=$HTTPS_PROXY"
fi

echo "📡 Proxy Configuration:"
echo "   HTTP_PROXY: $HTTP_PROXY"
echo "   HTTPS_PROXY: $HTTPS_PROXY"

# Check if we're in the right directory
if [ ! -d "web_gui" ]; then
    echo "❌ Error: web_gui directory not found!"
    echo "   Please run this script from the workshop-mcp-server directory"
    exit 1
fi

# Check if app.py exists
if [ ! -f "web_gui/app.py" ]; then
    echo "❌ Error: web_gui/app.py not found!"
    exit 1
fi

echo "🔧 Starting Flask dashboard..."
echo "📍 Dashboard will be available at: http://localhost:5001"
echo "🧪 Jira Manager (improved): http://localhost:5001/jira-manager-improved"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo "=========================================="

# Start the Flask app
cd web_gui
python3 app.py