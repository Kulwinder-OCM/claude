from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Flask App Working on Vercel!</h1>
            <p>This confirms the basic Flask setup is working correctly.</p>
            <a href="/full" class="btn btn-primary">Try Full App</a>
        </div>
    </body>
    </html>
    '''

@app.route('/full')
def full_app():
    return '''
    <div class="container mt-5">
        <h1>Full App Coming Soon</h1>
        <p>The basic Flask app is working. We can now add the full functionality.</p>
        <a href="/" class="btn btn-secondary">Back</a>
    </div>
    '''

# For local development
if __name__ == '__main__':
    app.run(debug=True)