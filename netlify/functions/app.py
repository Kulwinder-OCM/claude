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
    """Serve the main index page with Flask template rendering."""
    try:
        # Import Flask app components
        from config import config
        from ai_providers.ai_factory import AIProviderFactory

        # Get available providers
        available_providers = AIProviderFactory.list_available_providers()
        configured_providers = config.get_available_providers()

        # Filter to only show configured providers
        text_providers = []
        for provider, status in available_providers.items():
            if status.get("available") and configured_providers.get(provider, False):
                if provider in ["claude", "openai", "gemini"]:  # Text capable providers
                    text_providers.append(provider)

        # Read template files
        base_template_path = current_dir.parent.parent / 'templates' / 'base.html'
        index_template_path = current_dir.parent.parent / 'templates' / 'index.html'

        with open(base_template_path, 'r') as f:
            base_content = f.read()
        with open(index_template_path, 'r') as f:
            index_content = f.read()

        # Simple template rendering (replace Jinja2 syntax)
        # Replace template extends and block syntax with actual content
        rendered_content = base_content.replace('{% block content %}{% endblock %}',
                                              index_content.replace('{% extends "base.html" %}', '').replace('{% block content %}', '').replace('{% endblock %}', ''))

        # Replace template variables
        rendered_content = rendered_content.replace("{{ url_for('analyze') }}", "/analyze")

        # Replace provider loops with actual HTML
        provider_options = ""
        for provider in text_providers:
            selected = 'selected' if provider == 'claude' else ''
            provider_options += f'<option value="{provider}" {selected}>{provider.title()}</option>'

        # Replace all provider loops in the template
        import re
        # Replace text analysis provider options
        rendered_content = re.sub(
            r'{% for provider in text_providers %}.*?{% endfor %}',
            provider_options,
            rendered_content,
            flags=re.DOTALL
        )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': rendered_content
        }
    except Exception as e:
        print(f"Error serving index: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': f'<h1>Error loading page</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>'
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

        # Parse form data
        form_data = parse_qs(body)
        url = form_data.get('url', [None])[0]
        text_analysis_provider = form_data.get('text_analysis_provider', ['claude'])[0]
        text_generation_provider = form_data.get('text_generation_provider', ['claude'])[0]
        web_analysis_provider = form_data.get('web_analysis_provider', ['claude'])[0]
        content_strategy_provider = form_data.get('content_strategy_provider', ['claude'])[0]

        if not url:
            return serve_error_page('Please enter a valid URL')

        # Set environment variables for this request
        os.environ['AI_TEXT_ANALYSIS_PROVIDER'] = text_analysis_provider
        os.environ['AI_TEXT_GENERATION_PROVIDER'] = text_generation_provider
        os.environ['AI_WEB_ANALYSIS_PROVIDER'] = web_analysis_provider
        os.environ['AI_CONTENT_STRATEGY_PROVIDER'] = content_strategy_provider

        print(f"Starting analysis for URL: {url} with providers: text={text_analysis_provider}, web={web_analysis_provider}")

        # Import and run the orchestrator
        from orchestrator import BrandWorkflowOrchestrator

        orchestrator = BrandWorkflowOrchestrator()
        results = orchestrator.run_complete_workflow(url)

        # Generate session ID
        import time
        session_id = f"{url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')}-{int(time.time())}"

        # Return results page
        return serve_results_page_with_data(session_id, results)

    except Exception as e:
        print(f"Error in analyze handler: {e}")
        import traceback
        traceback.print_exc()
        return serve_error_page(f"Analysis failed: {str(e)}")

def serve_results_page_with_data(session_id, results):
    """Serve results page with actual workflow results."""
    try:
        # Read results template
        results_template_path = current_dir.parent.parent / 'templates' / 'results.html'
        base_template_path = current_dir.parent.parent / 'templates' / 'base.html'

        with open(base_template_path, 'r') as f:
            base_content = f.read()
        with open(results_template_path, 'r') as f:
            results_content = f.read()

        # Extract image information if available
        images = []
        if ('phases' in results and
            'brand_images' in results['phases'] and
            results['phases']['brand_images']['status'] == 'completed'):

            image_data = results['phases']['brand_images']['data']
            if 'images' in image_data:
                for img in image_data['images']:
                    if img.get('generation_status') == 'success':
                        images.append({
                            'filename': img['filename'],
                            'filepath': img['filepath'],
                            'concept': img.get('concept', 'Brand Image'),
                            'post_number': img.get('post_number', 1),
                            'file_size': img.get('file_size', 0)
                        })

        # Simple template rendering
        rendered_content = base_content.replace('{% block content %}{% endblock %}',
                                              results_content.replace('{% extends "base.html" %}', '').replace('{% block content %}', '').replace('{% endblock %}', ''))

        # Replace template variables with actual data
        workflow_status = results.get('workflow_status', 'unknown')

        # Create basic results HTML
        results_html = f"""
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div class="text-center mb-4">
                        <h1>Analysis Complete!</h1>
                        <p class="lead">Your brand analysis and campaign generation is ready.</p>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-primary text-white">
                                    <h5><i class="fas fa-chart-pie me-2"></i>Business Intelligence</h5>
                                </div>
                                <div class="card-body">
                                    <p>Status: <strong>{'Completed' if results.get('phases', {}).get('business_intel', {}).get('status') == 'completed' else 'Processing'}</strong></p>
                                </div>
                            </div>
                        </div>

                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-success text-white">
                                    <h5><i class="fas fa-palette me-2"></i>Design Analysis</h5>
                                </div>
                                <div class="card-body">
                                    <p>Status: <strong>{'Completed' if results.get('phases', {}).get('design_analysis', {}).get('status') == 'completed' else 'Processing'}</strong></p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-info text-white">
                                    <h5><i class="fas fa-bullhorn me-2"></i>Social Media Strategy</h5>
                                </div>
                                <div class="card-body">
                                    <p>Status: <strong>{'Completed' if results.get('phases', {}).get('social_content', {}).get('status') == 'completed' else 'Processing'}</strong></p>
                                </div>
                            </div>
                        </div>

                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-warning text-white">
                                    <h5><i class="fas fa-images me-2"></i>Generated Images</h5>
                                </div>
                                <div class="card-body">
                                    <p>Status: <strong>{'Completed' if results.get('phases', {}).get('brand_images', {}).get('status') == 'completed' else 'Processing'}</strong></p>
                                    <p>Images Generated: <strong>{len(images)}</strong></p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {"".join([f'''
                    <div class="card mb-3">
                        <div class="card-body">
                            <h6>{img['concept']} (Post {img['post_number']})</h6>
                            <p><strong>File:</strong> {img['filename']}</p>
                            <a href="/download/{img['filepath']}" class="btn btn-primary btn-sm">
                                <i class="fas fa-download me-1"></i>Download
                            </a>
                        </div>
                    </div>
                    ''' for img in images]) if images else ''}

                    <div class="text-center mt-4">
                        <a href="/" class="btn btn-outline-primary">
                            <i class="fas fa-arrow-left me-2"></i>Analyze Another Website
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """

        rendered_content = rendered_content.replace('{% block content %}{% endblock %}', results_html)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': rendered_content
        }

    except Exception as e:
        print(f"Error serving results: {e}")
        import traceback
        traceback.print_exc()
        return serve_error_page(f"Error displaying results: {str(e)}")

def serve_error_page(error_message):
    """Serve error page."""
    error_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error - Claude Life</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center mt-5">
                <div class="col-lg-6">
                    <div class="text-center">
                        <div class="alert alert-danger">
                            <h4 class="alert-heading"><i class="fas fa-exclamation-triangle me-2"></i>Error!</h4>
                            <p>{error_message}</p>
                        </div>
                        <a href="/" class="btn btn-primary">
                            <i class="fas fa-arrow-left me-2"></i>Go Back
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return {
        'statusCode': 500,
        'headers': {'Content-Type': 'text/html'},
        'body': error_html
    }

def serve_results_page(session_id):
    """Serve results page (placeholder)."""
    return serve_error_page(f'Session {session_id} not found')

def serve_status_api(session_id):
    """Serve status API (placeholder)."""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'status': 'unknown', 'message': 'Status API not implemented in serverless version'})
    }