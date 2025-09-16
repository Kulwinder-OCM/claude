#!/usr/bin/env python3
"""
Flask Web Application for Claude Life Brand Analysis - Vercel Version
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
        print(f"Index route error: {e}")
        import traceback
        traceback.print_exc()

        # Return a simple working HTML page
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Brand Analysis</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
        </head>
        <body>
            <div class="container mt-5">
                <h1 class="text-center mb-4">AI Brand Analysis & Campaign Generator</h1>
                <div class="alert alert-warning">
                    <strong>Debug Mode:</strong> Template loading failed: {str(e)}
                </div>

                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header">
                                <h3>Analyze Website</h3>
                            </div>
                            <div class="card-body">
                                <form method="POST" action="/analyze">
                                    <div class="mb-3">
                                        <label class="form-label">Website URL:</label>
                                        <input type="url" name="url" class="form-control" placeholder="https://example.com" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">AI Provider:</label>
                                        <select name="text_analysis_provider" class="form-control">
                                            <option value="claude">Claude</option>
                                            <option value="gemini">Gemini</option>
                                        </select>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Start Analysis</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
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

    # ALWAYS create the session first to avoid 404 errors
    workflow_results[session_id] = {
        'workflow_status': 'starting',
        'url': url,
        'timestamp': time.time(),
        'message': 'Initializing analysis...'
    }

    # Start workflow in background thread
    def run_workflow():
        # Update status to in_progress
        workflow_results[session_id] = {
            'workflow_status': 'in_progress',
            'url': url,
            'timestamp': time.time(),
            'message': 'Running AI analysis...'
        }

        try:
            print(f"=== Starting workflow for {url} ===")

            # Test if we can even import basic modules
            try:
                print("Testing basic imports...")
                import os
                import sys
                from pathlib import Path
                print("✓ Basic imports successful")

                # Check environment
                print(f"✓ Environment check:")
                print(f"  Current dir: {Path(__file__).parent}")
                print(f"  Parent dir: {Path(__file__).parent.parent}")
                print(f"  Python path entries: {len(sys.path)}")
                print(f"  CLAUDE_API_KEY: {'Set' if os.getenv('CLAUDE_API_KEY') else 'Missing'}")

                # Check if src directory exists
                src_path = Path(__file__).parent.parent / "src"
                print(f"  SRC directory exists: {src_path.exists()}")
                if src_path.exists():
                    print(f"  SRC contents: {[f.name for f in src_path.iterdir() if f.is_file()][:5]}")

            except Exception as e:
                raise Exception(f"Basic imports failed: {str(e)}")

            # Try to import the orchestrator
            try:
                print("Importing BrandWorkflowOrchestrator...")
                from orchestrator import BrandWorkflowOrchestrator
                print("✓ Successfully imported BrandWorkflowOrchestrator")
            except Exception as e:
                raise Exception(f"Failed to import BrandWorkflowOrchestrator: {str(e)}")

            # Update progress
            workflow_results[session_id].update({
                'workflow_status': 'initializing',
                'message': 'Setting up AI orchestrator...',
                'progress': 10
            })

            # Try to initialize orchestrator
            try:
                print("Initializing orchestrator...")
                orchestrator = BrandWorkflowOrchestrator()
                print("✓ BrandWorkflowOrchestrator initialized")

                # Test if basic methods exist
                print("Testing orchestrator methods...")
                if hasattr(orchestrator, 'run_complete_workflow'):
                    print("✓ run_complete_workflow method exists")
                else:
                    raise Exception("run_complete_workflow method not found")

            except Exception as e:
                raise Exception(f"Failed to initialize orchestrator: {str(e)}")

            # Update progress
            workflow_results[session_id].update({
                'workflow_status': 'running',
                'message': 'Running AI analysis workflow...',
                'progress': 30
            })

            # Try to run workflow with progress updates
            try:
                print("Running complete workflow...")

                # Run with shorter timeout and progress tracking
                def run_with_progress():
                    try:
                        results = orchestrator.run_complete_workflow(url)
                        return results
                    except Exception as e:
                        print(f"Workflow execution error: {e}")
                        raise e

                # Update progress during workflow
                workflow_results[session_id].update({
                    'workflow_status': 'analyzing',
                    'message': 'AI analyzing website content...',
                    'progress': 50
                })

                results = run_with_progress()
                print(f"✓ Workflow completed. Status: {results.get('workflow_status', 'unknown')}")

                # Ensure URL is in results
                results['url'] = url
                results['progress'] = 100
                workflow_results[session_id] = results

            except Exception as e:
                raise Exception(f"Workflow execution failed: {str(e)}")

        except Exception as e:
            print(f"✗ Workflow error: {e}")
            import traceback
            error_details = traceback.format_exc()
            print(f"✗ Full traceback: {error_details}")

            workflow_results[session_id] = {
                'error': str(e),
                'workflow_status': 'failed',
                'url': url,
                'traceback': error_details,
                'timestamp': time.time(),
                'debug_info': {
                    'python_path': sys.path[:3],  # First 3 entries
                    'current_dir': str(Path(__file__).parent),
                    'src_exists': (Path(__file__).parent.parent / "src").exists(),
                    'orchestrator_exists': (Path(__file__).parent.parent / "src" / "orchestrator.py").exists(),
                    'env_vars': {
                        'CLAUDE_API_KEY': 'set' if os.getenv('CLAUDE_API_KEY') else 'missing',
                        'GEMINI_API_KEY': 'set' if os.getenv('GEMINI_API_KEY') else 'missing'
                    }
                }
            }

    # Start the workflow thread
    thread = threading.Thread(target=run_workflow)
    thread.daemon = True
    thread.start()

    return redirect(url_for('results', session_id=session_id))

@app.route('/results/<session_id>')
def results(session_id):
    """Display results page for a specific analysis session."""
    if session_id not in workflow_results:
        return redirect(url_for('index'))

    results = workflow_results[session_id]

    # If still in progress, show loading page
    if results.get('workflow_status') == 'in_progress':
        try:
            return render_template('loading.html', session_id=session_id)
        except Exception as e:
            print(f"Loading template error: {e}")
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Analysis in Progress</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
                <meta http-equiv="refresh" content="5">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="text-center">
                        <div class="spinner-border text-primary mb-3" role="status"></div>
                        <h2>Analyzing {results.get('url', 'website')}...</h2>
                        <p>This may take a few minutes. Page will refresh automatically.</p>
                    </div>
                </div>
            </body>
            </html>
            '''

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

    try:
        return render_template('results.html',
                             results=results,
                             session_id=session_id,
                             images=images)
    except Exception as e:
        print(f"Results template error: {e}")
        # Create a simple results page
        status_class = "success" if results.get('workflow_status') == 'completed' else "danger"

        # Build detailed results HTML
        business_html = social_html = design_html = images_html = ""

        if results.get('phases'):
            # Business Intelligence
            if 'business_intel' in results['phases'] and results['phases']['business_intel'].get('data'):
                bi_data = results['phases']['business_intel']['data']
                business_html = f'''
                <div class="card mt-3">
                    <div class="card-header bg-info text-white">
                        <h5><i class="fas fa-building"></i> Business Intelligence</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Company:</strong> {bi_data.get('company_name', 'N/A')}</p>
                        <p><strong>Description:</strong> {bi_data.get('description', 'N/A')}</p>
                        <p><strong>Industry:</strong> {bi_data.get('industry', 'N/A')}</p>
                        <p><strong>Products/Services:</strong> {', '.join(bi_data.get('products_services', []))}</p>
                    </div>
                </div>
                '''

            # Social Content
            if 'social_content' in results['phases'] and results['phases']['social_content'].get('data'):
                sc_data = results['phases']['social_content']['data']
                if 'posts' in sc_data:
                    social_html = f'''
                    <div class="card mt-3">
                        <div class="card-header bg-success text-white">
                            <h5><i class="fas fa-share-alt"></i> Social Media Strategy</h5>
                        </div>
                        <div class="card-body">
                    '''
                    for i, post in enumerate(sc_data['posts'][:3], 1):
                        concept = post.get('concept', 'N/A') if isinstance(post, dict) else str(post)
                        caption = post.get('caption', 'N/A')[:200] if isinstance(post, dict) else 'N/A'
                        social_html += f'<div class="mb-3"><h6>Post {i}: {concept}</h6><p>{caption}{"..." if len(str(caption)) > 200 else ""}</p></div>'
                    social_html += '</div></div>'

            # Design Analysis
            if 'design_analysis' in results['phases'] and results['phases']['design_analysis'].get('data'):
                da_data = results['phases']['design_analysis']['data']
                design_html = f'''
                <div class="card mt-3">
                    <div class="card-header bg-warning text-white">
                        <h5><i class="fas fa-palette"></i> Design Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Colors:</strong> {', '.join(da_data.get('colors', []))}</p>
                        <p><strong>Fonts:</strong> {', '.join(da_data.get('fonts', []))}</p>
                        <p><strong>Visual Style:</strong> {da_data.get('visual_style', 'N/A')}</p>
                    </div>
                </div>
                '''

            # Generated Images
            if images:
                images_html = f'''
                <div class="card mt-3">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-images"></i> Generated Images ({len(images)} images)</h5>
                    </div>
                    <div class="card-body">
                '''
                for img in images:
                    images_html += f'''
                    <div class="mb-3 border p-3 rounded">
                        <h6>{img.get('concept', 'Brand Image')}</h6>
                        <p><strong>File:</strong> {img.get('filename', 'N/A')}</p>
                        <p><strong>Status:</strong> Successfully generated</p>
                        <a href="/download/{img.get('filepath', '')}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-download"></i> Download
                        </a>
                    </div>
                    '''
                images_html += '</div></div>'

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Complete</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="text-center mb-4">
                    <h1><i class="fas fa-check-circle text-success"></i> Analysis Complete!</h1>
                    <p class="lead">Successfully analyzed <strong>{results.get('url', 'website')}</strong></p>
                    <span class="badge bg-{status_class} fs-6 me-3">{results.get('workflow_status', 'unknown').replace('_', ' ').title()}</span>
                    <a href="/" class="btn btn-outline-primary">
                        <i class="fas fa-plus"></i> Analyze Another Site
                    </a>
                </div>

                {business_html}
                {social_html}
                {design_html}
                {images_html}

                {f'<div class="alert alert-danger mt-3"><h5>Error:</h5><p>{results.get("error")}</p></div>' if results.get('error') else ''}
                {f'<div class="alert alert-info mt-3">{results.get("message")}</div>' if results.get('message') else ''}
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
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
        'url': results.get('url', ''),
        'error': results.get('error'),
        'traceback': results.get('traceback'),
        'debug_info': results.get('debug_info', {})
    })

@app.route('/download/<path:filepath>')
def download_image(filepath):
    """Download generated images."""
    try:
        # Security: ensure the file is in the metrics directory
        full_path = Path(__file__).parent.parent / filepath
        if not str(full_path).startswith(str(Path(__file__).parent.parent / 'metrics')):
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
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'debug': 'Failed to load AI providers'
        })

@app.route('/debug')
def debug():
    """Debug endpoint to show all sessions and system info."""
    return jsonify({
        'active_sessions': list(workflow_results.keys()),
        'session_count': len(workflow_results),
        'session_details': {k: {'status': v.get('workflow_status', 'unknown'), 'url': v.get('url', 'unknown')} for k, v in workflow_results.items()},
        'python_path_count': len(sys.path),
        'current_time': time.time()
    })

@app.route('/test')
def test():
    """Test endpoint to check if basic imports work."""
    test_results = {
        'status': 'testing',
        'timestamp': time.time()
    }

    # Test imports
    try:
        import sys
        test_results['python_path'] = sys.path[:3]  # First 3 entries
        test_results['current_dir'] = str(Path(__file__).parent)
        test_results['parent_dir'] = str(Path(__file__).parent.parent)

        # Check if src directory exists
        src_path = Path(__file__).parent.parent / "src"
        test_results['src_exists'] = src_path.exists()

        if src_path.exists():
            test_results['src_contents'] = [f.name for f in src_path.iterdir() if f.is_file()][:10]

        # Test orchestrator import
        try:
            from orchestrator import BrandWorkflowOrchestrator
            test_results['orchestrator_import'] = 'success'
        except Exception as e:
            test_results['orchestrator_import'] = f'failed: {str(e)}'

        # Test config import
        try:
            from config import config
            test_results['config_import'] = 'success'
        except Exception as e:
            test_results['config_import'] = f'failed: {str(e)}'

        # Test AI factory import
        try:
            from ai_providers.ai_factory import AIProviderFactory
            test_results['ai_factory_import'] = 'success'
        except Exception as e:
            test_results['ai_factory_import'] = f'failed: {str(e)}'

        # Environment variables
        import os
        test_results['env_vars'] = {
            'CLAUDE_API_KEY': 'set' if os.getenv('CLAUDE_API_KEY') else 'missing',
            'GEMINI_API_KEY': 'set' if os.getenv('GEMINI_API_KEY') else 'missing',
            'SCREENSHOT_API_KEY': 'set' if os.getenv('SCREENSHOT_API_KEY') else 'missing'
        }

        test_results['status'] = 'completed'

    except Exception as e:
        import traceback
        test_results['status'] = 'failed'
        test_results['error'] = str(e)
        test_results['traceback'] = traceback.format_exc()

    return jsonify(test_results)

@app.route('/simple-test')
def simple_test():
    """Simple test that tries to run orchestrator directly without threading."""
    test_url = "https://example.com"
    result = {
        'test_url': test_url,
        'timestamp': time.time(),
        'steps': []
    }

    try:
        # Step 1: Import orchestrator
        result['steps'].append({'step': 1, 'action': 'importing orchestrator'})
        from orchestrator import BrandWorkflowOrchestrator
        result['steps'].append({'step': 1, 'status': 'success'})

        # Step 2: Initialize orchestrator
        result['steps'].append({'step': 2, 'action': 'initializing orchestrator'})
        orchestrator = BrandWorkflowOrchestrator()
        result['steps'].append({'step': 2, 'status': 'success'})

        # Step 3: Test a simple method (not full workflow)
        result['steps'].append({'step': 3, 'action': 'testing orchestrator methods'})
        if hasattr(orchestrator, 'run_complete_workflow'):
            result['steps'].append({'step': 3, 'status': 'success', 'message': 'Methods exist'})
        else:
            result['steps'].append({'step': 3, 'status': 'failed', 'message': 'Methods missing'})

        # Step 4: Try to run the workflow (this might hang)
        result['steps'].append({'step': 4, 'action': 'attempting workflow execution'})

        # Don't actually run it, just say we would
        result['steps'].append({'step': 4, 'status': 'skipped', 'message': 'Would run workflow here'})

        result['overall_status'] = 'success'

    except Exception as e:
        import traceback
        result['overall_status'] = 'failed'
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()

    return jsonify(result)

# Export the Flask app for Vercel
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)