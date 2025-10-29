
from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger  # Thêm import này
from dotenv import load_dotenv
import os

# Load .env located in the package directory (so importing from repo root still finds it)
package_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(package_dir, '.env')
load_dotenv(dotenv_path)

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

# Authentication configuration (switch between 'jwt' and 'oauth2')
# - AUTH_MODE: 'jwt' (default) or 'oauth2'
# - OAUTH2_INTROSPECTION_URL: URL of token introspection endpoint (RFC7662)
# - OAUTH2_INTROSPECTION_CLIENT_ID / _CLIENT_SECRET: optional client credentials
# - OAUTH2_USER_ID_FIELD: field in introspection response that contains the user identifier (default 'sub')
app.config.setdefault('AUTH_MODE', 'jwt')
app.config.setdefault('OAUTH2_INTROSPECTION_URL', None)
app.config.setdefault('OAUTH2_INTROSPECTION_CLIENT_ID', None)
app.config.setdefault('OAUTH2_INTROSPECTION_CLIENT_SECRET', None)
app.config.setdefault('OAUTH2_USER_ID_FIELD', 'sub')

# Google OAuth2 / OpenID Connect defaults
# Configure these in env or before app.run():
# - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_OAUTH_REDIRECT_URI
app.config.setdefault('GOOGLE_CLIENT_ID', None)
app.config.setdefault('GOOGLE_CLIENT_SECRET', None)
app.config.setdefault('GOOGLE_OAUTH_REDIRECT_URI', None)
app.config.setdefault('GOOGLE_OAUTH_SCOPES', 'openid email profile')

# Copy environment variables into app.config when present
for _k in (
    'SECRET_KEY',
    'AUTH_MODE',
    'OAUTH2_INTROSPECTION_URL',
    'OAUTH2_INTROSPECTION_CLIENT_ID',
    'OAUTH2_INTROSPECTION_CLIENT_SECRET',
    'OAUTH2_USER_ID_FIELD',
    'GOOGLE_CLIENT_ID',
    'GOOGLE_CLIENT_SECRET',
    'GOOGLE_OAUTH_REDIRECT_URI',
    'GOOGLE_OAUTH_SCOPES',
):
    v = os.getenv(_k)
    if v is not None:
        app.config[_k] = v

db = SQLAlchemy(app)
swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Library API",
        "description": "Simple API for library management (JWT Authentication supported)",
        "version": "1.0"
    },
    "basePath": "/api", 
    "securityDefinitions": {  
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
        }
    },
    "security": [ 
        {"Bearer": []}
    ]
})


from .models import BookTitle, BookCopy, User, Borrowing
from .api import api as api_blueprint

app.register_blueprint(api_blueprint)

# ==========================================
# Frontend Routes (HTML pages)
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/register.html')
def register_page():
    return render_template('register.html')

@app.route('/google-callback.html')
def google_callback_page():
    return render_template('google_callback.html')

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

with app.app_context():
    db.create_all()