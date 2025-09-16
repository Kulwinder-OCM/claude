#!/bin/bash
echo "🚀 Starting Claude Life Web Application..."
echo "📍 Make sure you have set up your API keys in environment variables:"
echo "   - CLAUDE_API_KEY"
echo "   - GEMINI_API_KEY"
echo "   - OPENAI_API_KEY (optional)"
echo ""
echo "🌐 Web interface will be available at:"
echo "   http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Activate virtual environment and start the Flask app
source venv/bin/activate
python app.py