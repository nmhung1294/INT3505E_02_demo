# library_app/__init__.py (cập nhật)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger  # Thêm import này

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# Init Swagger với config cơ bản
swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Library API",
        "description": "Simple API for library management",
        "version": "1.0"
    },
    "basePath": "/api"  # Prefix cho tất cả API routes
})

# Import models và routes sau app/db
from .models import Book, User, Borrowing
from .api import api as api_blueprint  # Thêm blueprint cho API

app.register_blueprint(api_blueprint, url_prefix='/api')  # Mount API tại /api

# Create database tables
with app.app_context():
    db.create_all()