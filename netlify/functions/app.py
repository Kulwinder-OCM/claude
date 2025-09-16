import json
import os
import sys
from urllib.parse import parse_qs

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', '..', 'src')
sys.path.insert(0, src_path)

from config import Config
from agents.brand_workflow_orchestrator import BrandWorkflowOrchestrator

def handler(event, context):
    """Netlify function handler for the brand analysis workflow."""

    try:
        # Handle preflight OPTIONS requests
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                }
            }

        # Only handle POST requests
        if event.get('httpMethod') != 'POST':
            return {
                'statusCode': 405,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }

        # Parse request body
        body = event.get('body', '{}')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            # Handle form data
            data = parse_qs(body)
            data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in data.items()}

        url = data.get('url')
        if not url:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'URL is required'})
            }

        # Initialize configuration
        config = Config()

        # Run the brand workflow
        orchestrator = BrandWorkflowOrchestrator()
        result = orchestrator.process(url)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'data': result
            })
        }

    except Exception as e:
        print(f"Error in Netlify function: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }