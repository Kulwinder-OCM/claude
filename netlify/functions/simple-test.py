def handler(event, context):
    """Simple test to verify Python functions work"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Flask App</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>Python Function Working!</h1>
                <p>If you see this, the Python function is running correctly.</p>
                <form method="POST" action="/.netlify/functions/app">
                    <div class="mb-3">
                        <label class="form-label">Website URL:</label>
                        <input type="url" name="url" class="form-control" placeholder="https://example.com" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Test Analysis</button>
                </form>
            </div>
        </body>
        </html>
        '''
    }