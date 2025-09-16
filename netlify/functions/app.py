import os
import sys
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import the Flask app
from app import app

def handler(event, context):
    """Netlify function handler that wraps the Flask application."""
    try:
        from werkzeug.test import Client
        from werkzeug.wrappers import BaseResponse

        # Create a test client to simulate the request
        client = Client(app, BaseResponse)

        # Convert Netlify event to Flask request format
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_string = event.get('queryStringParameters') or {}
        headers = event.get('headers', {})
        body = event.get('body', '')

        # Build query string
        query_parts = []
        for key, value in query_string.items():
            if value is not None:
                query_parts.append(f"{key}={value}")
        query_str = '&'.join(query_parts)

        # Make the request to Flask app
        if method == 'GET':
            response = client.get(path, query_string=query_str, headers=headers)
        elif method == 'POST':
            response = client.post(path, data=body, headers=headers, query_string=query_str)
        else:
            response = client.open(method=method, path=path, data=body, headers=headers, query_string=query_str)

        # Convert Flask response to Netlify format
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }

    except Exception as e:
        print(f"Error in Netlify function: {e}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/html'
            },
            'body': f"<h1>Internal Server Error</h1><p>{str(e)}</p>"
        }