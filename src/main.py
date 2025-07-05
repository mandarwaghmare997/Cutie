import os
import sys
from datetime import timedelta
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and routes
from src.models.user import db
from src.routes.auth import auth_bp
from src.routes.assessment import assessment_bp
from src.routes.file_management import file_bp
from src.routes.admin import admin_bp
from src.routes.certificate import certificate_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'qryti-compliance-platform-secret-key-2025')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'qryti-jwt-secret-key-2025')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# AWS Configuration (for production deployment)
app.config['AWS_REGION'] = os.getenv('AWS_REGION', 'us-east-1')
app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize extensions
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])
jwt = JWTManager(app)

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(assessment_bp, url_prefix='/api/assessments')
app.register_blueprint(file_bp, url_prefix='/api/files')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(certificate_bp, url_prefix='/api/certificates')

# Create database tables
with app.app_context():
    db.create_all()

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'token_expired', 'message': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'invalid_token', 'message': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'authorization_required', 'message': 'Authorization token required'}), 401

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'ISO 42001 Compliance Platform',
        'version': '1.0.0'
    })

# Admin dashboard route
@app.route('/admin')
def serve_admin():
    admin_path = os.path.join(app.static_folder, 'pages', 'admin.html')
    if os.path.exists(admin_path):
        return send_from_directory(os.path.join(app.static_folder, 'pages'), 'admin.html')
    else:
        return "Admin dashboard not found", 404

# Serve frontend application
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({
                'message': 'ISO 42001 Compliance Platform API',
                'version': '1.0.0',
                'endpoints': {
                    'health': '/api/health',
                    'auth': '/api/auth/*',
                    'assessments': '/api/assessments/*',
                    'files': '/api/files/*',
                    'admin': '/api/admin/*'
                }
            })

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

