from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from gateway import gateway_bp

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS
CORS(app)

# Register blueprints
app.register_blueprint(gateway_bp)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "services": {
            "ai_agent": "pending check",
            "database": "pending check"
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)