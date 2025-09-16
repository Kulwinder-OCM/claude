#!/usr/bin/env python3
"""
Flask Web Application for Claude Life Brand Analysis - Vercel Compatible
"""

import sys
import json
import os
import time
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for

# Add src to path (adjust for api directory structure)
sys.path.append(str(Path(__file__).parent.parent / "src"))

app = Flask(__name__,
           template_folder='../templates',
           static_folder='../static')
app.secret_key = 'claude-life-secret-key-2025'

# Global variable to store workflow results
workflow_results = {}

@app.route('/')
def index():
    """Main page with form for URL input and AI model selection."""
    try:
        # Import modules for provider selection
        from ai_providers.ai_factory import AIProviderFactory
        from config import config

        # Get available providers
        available_providers = AIProviderFactory.list_available_providers()
        configured_providers = config.get_available_providers()

        # Filter to only show configured providers
        text_providers = []
        for provider, status in available_providers.items():
            if status.get("available") and configured_providers.get(provider, False):
                if provider in ["claude", "openai", "gemini"]:  # Text capable providers
                    text_providers.append(provider)

        return render_template('index.html', text_providers=text_providers)

    except Exception as e:
        print(f"Template/Import error: {e}")
        # Fallback to default providers if imports fail
        text_providers = ["claude", "gemini"]

        # If template rendering fails, return a simple HTML form
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Brand Analysis</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>AI Brand Analysis & Campaign Generator</h1>
                <div class="alert alert-warning">Template error: {str(e)}</div>
                <form method="POST" action="/analyze">
                    <div class="mb-3">
                        <label class="form-label">Website URL:</label>
                        <input type="url" name="url" class="form-control" placeholder="https://example.com" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">AI Provider:</label>
                        <select name="text_analysis_provider" class="form-control">
                            {' '.join([f'<option value="{p}">{p.title()}</option>' for p in text_providers])}
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Analyze Website</button>
                </form>
            </div>
        </body>
        </html>
        '''

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle URL analysis with selected AI providers."""
    url = request.form.get('url')
    text_analysis_provider = request.form.get('text_analysis_provider', 'claude')
    text_generation_provider = request.form.get('text_generation_provider', 'claude')
    web_analysis_provider = request.form.get('web_analysis_provider', 'claude')
    content_strategy_provider = request.form.get('content_strategy_provider', 'claude')
    
    if not url:
        flash('Please enter a valid URL', 'error')
        return redirect(url_for('index'))
    
    # Set environment variables for this request
    os.environ['AI_TEXT_ANALYSIS_PROVIDER'] = text_analysis_provider
    os.environ['AI_TEXT_GENERATION_PROVIDER'] = text_generation_provider
    os.environ['AI_WEB_ANALYSIS_PROVIDER'] = web_analysis_provider
    os.environ['AI_CONTENT_STRATEGY_PROVIDER'] = content_strategy_provider
    
    # Generate a unique session ID for this analysis
    session_id = f"{url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')}-{int(time.time())}"
    
    # Start workflow in background thread
    def run_workflow():
        try:
            print(f"Starting real workflow for {url}")
            from orchestrator import BrandWorkflowOrchestrator
            orchestrator = BrandWorkflowOrchestrator()
            results = orchestrator.run_complete_workflow(url)
            workflow_results[session_id] = results
            print(f"Workflow completed for {url}")
        except Exception as e:
            print(f"Workflow error: {e}")
            import traceback
            workflow_results[session_id] = {
                'error': str(e),
                'workflow_status': 'failed',
                'url': url,
                'traceback': traceback.format_exc()
            }
    
    # Start the workflow
    workflow_results[session_id] = {'workflow_status': 'in_progress'}
    thread = threading.Thread(target=run_workflow)
    thread.daemon = True
    thread.start()
    
    return redirect(url_for('results', session_id=session_id))

@app.route('/results/<session_id>')
def results(session_id):
    """Display results page for a specific analysis session."""
    if session_id not in workflow_results:
        return redirect(url_for('index'))

    results_data = workflow_results[session_id]

    # If still in progress, show loading page
    if results_data.get('workflow_status') == 'in_progress':
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis in Progress</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <meta http-equiv="refresh" content="5">
        </head>
        <body>
            <div class="container mt-5">
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status"></div>
                    <h2>Analyzing {results_data.get('url', 'website')}...</h2>
                    <p>This may take a few minutes. Page will refresh automatically.</p>
                </div>
            </div>
        </body>
        </html>
        '''

    # Try to render template, fallback to HTML if templates not available
    try:
        # Extract image information if available
        images = []
        if ('phases' in results_data and
            'brand_images' in results_data['phases'] and
            results_data['phases']['brand_images']['status'] == 'completed'):

            image_data = results_data['phases']['brand_images']['data']
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

        return render_template('results.html',
                             results=results_data,
                             session_id=session_id,
                             images=images)
    except Exception as e:
        print(f"Template error: {e}")
        # Fallback HTML response
        status_class = "success" if results_data.get('workflow_status') == 'completed' else "danger"

        phases_html = ""
        if results_data.get('phases'):
            phases_html = "<h4>Analysis Phases:</h4><ul class='list-group mb-3'>"
            for phase, data in results_data['phases'].items():
                phase_status = data.get('status', 'unknown')
                phase_class = "success" if phase_status == 'completed' else "warning"
                phases_html += f'<li class="list-group-item list-group-item-{phase_class}">'
                phases_html += f'<strong>{phase.replace("_", " ").title()}:</strong> {phase_status}'
                if data.get('message'):
                    phases_html += f'<br><small>{data["message"]}</small>'
                phases_html += '</li>'
            phases_html += "</ul>"

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Complete</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>Analysis Complete!</h1>
                <div class="alert alert-{status_class}">
                    <h4>Analysis Results for: {results_data.get('url', 'Unknown URL')}</h4>
                    <p><strong>Status:</strong> {results_data.get('workflow_status', 'unknown')}</p>
                </div>

                {phases_html}

                {f'<div class="alert alert-danger"><h5>Error Details:</h5><p>{results_data.get("error")}</p></div>' if results_data.get('error') else ''}
                {f'<div class="alert alert-info">{results_data.get("message")}</div>' if results_data.get('message') else ''}
                {f'<details><summary>Technical Details</summary><pre class="mt-2">{results_data.get("traceback")}</pre></details>' if results_data.get('traceback') else ''}

                <div class="mt-4">
                    <a href="/" class="btn btn-primary">Analyze Another Website</a>
                    <a href="/status/{session_id}" class="btn btn-outline-secondary ms-2">Check Status API</a>
                </div>
            </div>
        </body>
        </html>
        '''

@app.route('/status/<session_id>')
def status(session_id):
    """API endpoint to check workflow status."""
    if session_id not in workflow_results:
        return jsonify({'error': 'Session not found'}), 404
    
    results = workflow_results[session_id]
    return jsonify({
        'status': results.get('workflow_status', 'unknown'),
        'phases': results.get('phases', {}),
        'error': results.get('error')
    })

@app.route('/download/<path:filepath>')
def download_image(filepath): 
    """Download generated images."""
    try:
        # Security: ensure the file is in the metrics directory
        full_path = Path(__file__).parent / filepath
        if not str(full_path).startswith(str(Path(__file__).parent / 'metrics')):
            return "Access denied", 403
        
        if full_path.exists() and full_path.is_file():
            return send_file(full_path, as_attachment=True)
        else:
            return "File not found", 404
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

@app.route('/providers')
def providers():
    """API endpoint to get available providers."""
    try:
        from ai_providers.ai_factory import AIProviderFactory
        from config import config

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

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Could not load providers: {str(e)}'})

# Export the Flask app for Vercel
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)