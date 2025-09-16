import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote
import base64

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def handler(event, context):
    """Netlify function handler for the brand analysis application."""
    try:
        print(f"Event: {json.dumps(event, default=str)}")

        # Handle different types of requests
        method = event.get('httpMethod', 'GET').upper()
        path = event.get('path', '/')

        # Remove the function path prefix if present
        if path.startswith('/netlify/functions/app'):
            path = path.replace('/netlify/functions/app', '') or '/'

        print(f"Processing {method} {path}")

        # Handle GET requests (main page, static content)
        if method == 'GET':
            if path == '/' or path == '/index.html':
                return serve_index_page()
            elif path.startswith('/static/'):
                return serve_static_file(path)
            elif path.startswith('/results/'):
                session_id = path.split('/')[-1]
                return serve_results_page(session_id)
            elif path.startswith('/status/'):
                session_id = path.split('/')[-1]
                return serve_status_api(session_id)
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'text/html'},
                    'body': '<h1>Page not found</h1>'
                }

        # Handle POST requests (form submissions)
        elif method == 'POST':
            if path == '/analyze' or path == '/':
                return handle_analyze_request(event)
            else:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': False, 'error': 'Endpoint not found'})
                }

        # Handle OPTIONS requests (CORS preflight)
        elif method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': ''
            }

        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'success': False, 'error': 'Method not allowed'})
            }

    except Exception as e:
        print(f"Error in handler: {e}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': f'<h1>Internal Server Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>'
        }

def serve_index_page():
    """Serve the main index page."""
    try:
        template_path = current_dir.parent.parent / 'templates' / 'index.html'
        with open(template_path, 'r') as f:
            html_content = f.read()

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html_content
        }
    except Exception as e:
        print(f"Error serving index: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': f'<h1>Error loading page</h1><p>{str(e)}</p>'
        }

def serve_static_file(path):
    """Serve static files."""
    try:
        file_path = current_dir.parent.parent / path.lstrip('/')

        if not file_path.exists():
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'text/plain'},
                'body': 'File not found'
            }

        # Determine content type
        if path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        else:
            content_type = 'text/plain'

        # Read file
        if content_type.startswith('image/'):
            with open(file_path, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': content_type},
                'body': file_content,
                'isBase64Encoded': True
            }
        else:
            with open(file_path, 'r') as f:
                file_content = f.read()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': content_type},
                'body': file_content
            }

    except Exception as e:
        print(f"Error serving static file {path}: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': f'Error serving file: {str(e)}'
        }

def handle_analyze_request(event):
    """Handle the analyze form submission."""
    try:
        # Parse request body
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')

        url = None

        # Try to parse as JSON first
        try:
            json_data = json.loads(body)
            url = json_data.get('url')
        except json.JSONDecodeError:
            # Fall back to form data parsing
            form_data = parse_qs(body)
            url = form_data.get('url', [None])[0]

        if not url:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'success': False, 'error': 'URL is required'})
            }

        print(f"Starting analysis for URL: {url}")

        # Import and run the orchestrator
        from orchestrator import BrandWorkflowOrchestrator

        orchestrator = BrandWorkflowOrchestrator()
        results = orchestrator.run_complete_workflow(url)

        # Generate session ID
        import time
        session_id = f"{url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')}-{int(time.time())}"

        # Return JSON response for API calls
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': results,
                'workflow_status': results.get('workflow_status', 'unknown'),
                'url': url,
                'session_id': session_id
            })
        }

    except Exception as e:
        print(f"Error in analyze handler: {e}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f"Analysis failed: {str(e)}",
                'details': traceback.format_exc()
            })
        }

def serve_results_page(session_id):
    """Serve results page (placeholder)."""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': f'<h1>Results for session {session_id}</h1><p>Feature not implemented in serverless version</p><a href="/">← Back</a>'
    }

def serve_status_api(session_id):
    """Serve status API (placeholder)."""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'status': 'unknown', 'message': 'Status API not implemented in serverless version'})
    }