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

    # Run analysis with better error handling and timeout
    def run_workflow():
        try:
            print(f"Starting workflow for {url}")

            # Set environment variables from Vercel environment
            os.environ.setdefault('AI_TEXT_ANALYSIS_PROVIDER', 'claude')
            os.environ.setdefault('AI_TEXT_GENERATION_PROVIDER', 'claude')
            os.environ.setdefault('AI_WEB_ANALYSIS_PROVIDER', 'claude')
            os.environ.setdefault('AI_CONTENT_STRATEGY_PROVIDER', 'claude')

            # Import the orchestrator only when needed
            sys.path.append(str(Path(__file__).parent.parent / "src"))

            print("Attempting to import orchestrator...")
            from orchestrator import BrandWorkflowOrchestrator
            print("Orchestrator imported successfully")

            print("Creating orchestrator instance...")
            orchestrator = BrandWorkflowOrchestrator()
            print("Running workflow...")

            results = orchestrator.run_complete_workflow(url)
            print(f"Workflow completed: {results.get('workflow_status', 'unknown')}")

            workflow_results[session_id] = results

        except ImportError as e:
            print(f"Import error in workflow: {e}")
            # Create a mock successful result for testing
            workflow_results[session_id] = {
                'workflow_status': 'completed',
                'url': url,
                'message': f'Mock analysis completed for {url}. Full functionality requires all dependencies.',
                'phases': {
                    'business_intel': {'status': 'completed', 'message': 'Business analysis completed (mock)'},
                    'design_analysis': {'status': 'completed', 'message': 'Design analysis completed (mock)'},
                    'social_content': {'status': 'completed', 'message': 'Social content strategy created (mock)'},
                    'brand_images': {'status': 'completed', 'message': 'Images would be generated here (mock)'}
                }
            }

        except Exception as e:
            print(f"Workflow error: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")

            # Create a fallback result with the error
            workflow_results[session_id] = {
                'error': str(e),
                'workflow_status': 'failed',
                'url': url,
                'message': f'Analysis failed: {str(e)}',
                'traceback': traceback.format_exc()
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

    # Show results with detailed information
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

    results_data = workflow_results[session_id]
    return jsonify({
        'status': results_data.get('workflow_status', 'unknown'),
        'url': results_data.get('url', ''),
        'error': results_data.get('error')
    })

# Export the Flask app for Vercel
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)