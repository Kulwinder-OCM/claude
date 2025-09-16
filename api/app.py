#!/usr/bin/env python3
"""
Simplified Flask Web Application for Claude Life Brand Analysis - Vercel Compatible
"""

import sys
import json
import os
import time
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for

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
        # Try to import modules, but don't fail if they're not available
        try:
            sys.path.append(str(Path(__file__).parent.parent / "src"))
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
        except ImportError as e:
            print(f"Import error: {e}")
            # Fallback to default providers if imports fail
            text_providers = ["claude", "gemini"]

        return render_template('index.html', text_providers=text_providers)

    except Exception as e:
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

    if not url:
        return redirect(url_for('index'))

    # Generate a unique session ID for this analysis
    session_id = f"{url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')}-{int(time.time())}"

    # For now, simulate the analysis process
    def run_workflow():
        try:
            # Import the orchestrator only when needed
            sys.path.append(str(Path(__file__).parent.parent / "src"))
            from orchestrator import BrandWorkflowOrchestrator

            orchestrator = BrandWorkflowOrchestrator()
            results = orchestrator.run_complete_workflow(url)
            workflow_results[session_id] = results
        except Exception as e:
            print(f"Workflow error: {e}")
            # Create a fallback result
            workflow_results[session_id] = {
                'error': str(e),
                'workflow_status': 'failed',
                'url': url,
                'message': 'Analysis completed with limited functionality due to serverless constraints'
            }

    # Start the workflow (same as local app.py)
    workflow_results[session_id] = {'workflow_status': 'in_progress', 'url': url}
    thread = threading.Thread(target=run_workflow)
    thread.daemon = True
    thread.start()

    return redirect(url_for('results', session_id=session_id))

@app.route('/results/<session_id>')
def results(session_id):
    """Display results page for a specific analysis session."""
    if session_id not in workflow_results:
        return f'''
        <div class="container mt-5">
            <div class="alert alert-danger">Analysis session not found</div>
            <a href="/" class="btn btn-primary">Start New Analysis</a>
        </div>
        '''

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

    # Show results
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
            <div class="alert alert-success">
                <h4>Analysis Results for: {results_data.get('url', 'Unknown URL')}</h4>
                <p>Status: {results_data.get('workflow_status', 'unknown')}</p>
            </div>

            {f'<div class="alert alert-warning">Error: {results_data.get("error")}</div>' if results_data.get('error') else ''}
            {f'<div class="alert alert-info">{results_data.get("message")}</div>' if results_data.get('message') else ''}

            <a href="/" class="btn btn-primary">Analyze Another Website</a>
        </div>
    </body>
    </html>
    '''

@app.route('/status/<session_id>')
def status(session_id):
    """API endpoint to check workflow status."""
    if session_id not in workflow_results:
        return jsonify({'error': 'Session not found'}), 404

    results_data = workflow_results[session_id]
    return jsonify({
        'status': results_data.get('workflow_status', 'unknown'),
        'url': results_data.get('url', ''),
        'error': results_data.get('error')
    })

# Export the Flask app for Vercel
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)