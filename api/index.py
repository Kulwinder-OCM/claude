#!/usr/bin/env python3
"""
Flask Web Application for Claude Life Brand Analysis
"""

import sys
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import threading
import time
import os

# Add src to path (adjust for api directory structure)
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import config module which automatically loads environment variables (same as CLI)
# This ensures identical environment loading to the CLI

from orchestrator import BrandWorkflowOrchestrator
from ai_providers.ai_factory import AIProviderFactory
from config import config

app = Flask(__name__)
app.secret_key = 'claude-life-secret-key-2025'

# Global variable to store workflow results
workflow_results = {}

@app.route('/')
def index():
    """Main page with form for URL input and AI model selection."""
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
            orchestrator = BrandWorkflowOrchestrator()
            results = orchestrator.run_complete_workflow(url)
            workflow_results[session_id] = results
        except Exception as e:
            print(f"Workflow error: {e}")
            workflow_results[session_id] = {'error': str(e), 'workflow_status': 'failed'}
    
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
        flash('Analysis session not found', 'error')
        return redirect(url_for('index'))
    
    results = workflow_results[session_id]
    
    # If still in progress, show loading page
    if results['workflow_status'] == 'in_progress':
        return render_template('loading.html', session_id=session_id)
    
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
    
    return render_template('results.html', 
                         results=results, 
                         session_id=session_id, 
                         images=images)

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

# Export the Flask app for Vercel
# Vercel will automatically handle WSGI conversion
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)