#!/usr/bin/env python3
"""
Netlify Function for Claude Life Brand Analysis
Based on the Flask Web Application structure
"""

import sys
import json
import os
import time
import threading
from pathlib import Path
from urllib.parse import parse_qs, unquote
import base64

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import Flask app components (same as local app.py)
from orchestrator import BrandWorkflowOrchestrator
from ai_providers.ai_factory import AIProviderFactory
from config import config

# Global variable to store workflow results (same as local app.py)
workflow_results = {}

def handler(event, context):
    """Netlify function handler for the brand analysis application."""
    try:
        print(f"Event: {json.dumps(event, default=str)}")

        # Handle different types of requests
        method = event.get('httpMethod', 'GET').upper()
        path = event.get('path', '/')

        # Remove the function path prefix if present
        if path.startswith('/.netlify/functions/app'):
            path = path.replace('/.netlify/functions/app', '') or '/'

        print(f"Processing {method} {path}")

        # Route handling - exact match to Flask app routes
        if method == 'GET':
            if path == '/' or path == '/index.html':
                return flask_index()
            elif path.startswith('/static/'):
                return serve_static_file(path)
            elif path.startswith('/results/'):
                session_id = path.split('/')[-1]
                return flask_results(session_id)
            elif path.startswith('/status/'):
                session_id = path.split('/')[-1]
                return flask_status_api(session_id)
            elif path.startswith('/download/'):
                filepath = path.replace('/download/', '')
                return flask_download_image(filepath)
            elif path == '/providers':
                return flask_providers_api()
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'text/html'},
                    'body': '<h1>Page not found</h1>'
                }

        # Handle POST requests (form submissions)
        elif method == 'POST':
            if path == '/analyze':
                return flask_analyze(event)
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

# Flask route functions - exact duplicates from local app.py
def flask_index():
    """Main page with form for URL input and AI model selection - exact copy from Flask app."""
    try:
        # Get available providers (same as local app.py)
        available_providers = AIProviderFactory.list_available_providers()
        configured_providers = config.get_available_providers()

        # Filter to only show configured providers (same as local app.py)
        text_providers = []
        for provider, status in available_providers.items():
            if status.get("available") and configured_providers.get(provider, False):
                if provider in ["claude", "openai", "gemini"]:  # Text capable providers
                    text_providers.append(provider)

        # Simple template rendering for serverless
        return render_template_serverless('index.html', {'text_providers': text_providers})
    except Exception as e:
        print(f"Error in flask_index: {e}")
        import traceback
        traceback.print_exc()
        return serve_error_page(f"Error loading page: {str(e)}")

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

def flask_analyze(event):
    """Handle URL analysis with selected AI providers - exact copy from Flask app."""
    try:
        # Parse request body
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')

        # Parse form data (same as request.form.get in Flask)
        form_data = parse_qs(body)
        url = form_data.get('url', [None])[0]
        text_analysis_provider = form_data.get('text_analysis_provider', ['claude'])[0]
        text_generation_provider = form_data.get('text_generation_provider', ['claude'])[0]
        web_analysis_provider = form_data.get('web_analysis_provider', ['claude'])[0]
        content_strategy_provider = form_data.get('content_strategy_provider', ['claude'])[0]

        if not url:
            # Same behavior as Flask app - redirect to index with error
            return serve_error_page('Please enter a valid URL')

        # Set environment variables for this request (same as local app.py)
        os.environ['AI_TEXT_ANALYSIS_PROVIDER'] = text_analysis_provider
        os.environ['AI_TEXT_GENERATION_PROVIDER'] = text_generation_provider
        os.environ['AI_WEB_ANALYSIS_PROVIDER'] = web_analysis_provider
        os.environ['AI_CONTENT_STRATEGY_PROVIDER'] = content_strategy_provider

        # Generate a unique session ID for this analysis (same as local app.py)
        session_id = f"{url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')}-{int(time.time())}"

        # Start workflow in background thread (same as local app.py)
        def run_workflow():
            try:
                orchestrator = BrandWorkflowOrchestrator()
                results = orchestrator.run_complete_workflow(url)
                workflow_results[session_id] = results
            except Exception as e:
                print(f"Workflow error: {e}")
                workflow_results[session_id] = {'error': str(e), 'workflow_status': 'failed'}

        # Start the workflow (same as local app.py)
        workflow_results[session_id] = {'workflow_status': 'in_progress'}
        thread = threading.Thread(target=run_workflow)
        thread.daemon = True
        thread.start()

        # Redirect to results page (same as local app.py)
        return redirect_to_results(session_id)

    except Exception as e:
        print(f"Error in flask_analyze: {e}")
        import traceback
        traceback.print_exc()
        return serve_error_page(f"Analysis failed: {str(e)}")

def flask_results(session_id):
    """Display results page for a specific analysis session - exact copy from Flask app."""
    try:
        if session_id not in workflow_results:
            return serve_error_page('Analysis session not found')

        results = workflow_results[session_id]

        # If still in progress, show loading page (same as local app.py)
        if results['workflow_status'] == 'in_progress':
            return render_template_serverless('loading.html', {'session_id': session_id})

        # Extract image information if available (same as local app.py)
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

        return render_template_serverless('results.html', {
            'results': results,
            'session_id': session_id,
            'images': images
        })
    except Exception as e:
        print(f"Error in flask_results: {e}")
        import traceback
        traceback.print_exc()
        return serve_error_page(f"Error displaying results: {str(e)}")

def flask_status_api(session_id):
    """API endpoint to check workflow status - exact copy from Flask app."""
    if session_id not in workflow_results:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Session not found'})
        }

    results = workflow_results[session_id]
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'status': results.get('workflow_status', 'unknown'),
            'phases': results.get('phases', {}),
            'error': results.get('error')
        })
    }

def flask_download_image(filepath):
    """Download generated images - exact copy from Flask app."""
    try:
        # Security: ensure the file is in the metrics directory (same as local app.py)
        full_path = project_root / filepath
        if not str(full_path).startswith(str(project_root / 'metrics')):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'text/plain'},
                'body': 'Access denied'
            }

        if full_path.exists() and full_path.is_file():
            with open(full_path, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode()

            # Determine content type
            if filepath.endswith('.png'):
                content_type = 'image/png'
            elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
                content_type = 'image/jpeg'
            else:
                content_type = 'application/octet-stream'

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': content_type,
                    'Content-Disposition': f'attachment; filename="{full_path.name}"'
                },
                'body': file_content,
                'isBase64Encoded': True
            }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'text/plain'},
                'body': 'File not found'
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': f'Error downloading file: {str(e)}'
        }

def flask_providers_api():
    """API endpoint to get available providers - exact copy from Flask app."""
    try:
        available = AIProviderFactory.list_available_providers()
        configured = config.get_available_providers()

        result = {}
        for provider, status in available.items():
            if status.get("available") and configured.get(provider, False):
                result[provider] = {
                    'available': True,
                    'capabilities': status.get('capabilities', [])
                }
            else:
                result[provider] = {'available': False}

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

# Helper functions for serverless environment
def redirect_to_results(session_id):
    """Redirect to results page (serverless equivalent of Flask redirect)."""
    return {
        'statusCode': 302,
        'headers': {
            'Location': f'/results/{session_id}',
            'Content-Type': 'text/html'
        },
        'body': f'<html><head><meta http-equiv="refresh" content="0;url=/results/{session_id}"></head><body>Redirecting...</body></html>'
    }

def render_template_serverless(template_name, context=None):
    """Render templates for serverless environment (equivalent of Flask render_template)."""
    try:
        if context is None:
            context = {}

        # Read template files
        base_template_path = project_root / 'templates' / 'base.html'
        template_path = project_root / 'templates' / template_name

        with open(base_template_path, 'r') as f:
            base_content = f.read()
        with open(template_path, 'r') as f:
            template_content = f.read()

        # Simple template rendering (replace Jinja2 syntax)
        rendered_content = base_content.replace('{% block content %}{% endblock %}',
                                              template_content.replace('{% extends "base.html" %}', '').replace('{% block content %}', '').replace('{% endblock %}', ''))

        # Replace template variables
        rendered_content = rendered_content.replace("{{ url_for('analyze') }}", "/analyze")

        # Replace provider loops with actual HTML if text_providers in context
        if 'text_providers' in context:
            provider_options = ""
            for provider in context['text_providers']:
                selected = 'selected' if provider == 'claude' else ''
                provider_options += f'<option value="{provider}" {selected}>{provider.title()}</option>'

            # Replace all provider loops in the template
            import re
            rendered_content = re.sub(
                r'{% for provider in text_providers %}.*?{% endfor %}',
                provider_options,
                rendered_content,
                flags=re.DOTALL
            )

        # Handle session_id and other context variables
        if 'session_id' in context:
            rendered_content = rendered_content.replace('{{ session_id }}', context['session_id'])

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': rendered_content
        }
    except Exception as e:
        print(f"Error in render_template_serverless: {e}")
        import traceback
        traceback.print_exc()
        return serve_error_page(f"Template rendering error: {str(e)}")

# Error handling function
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