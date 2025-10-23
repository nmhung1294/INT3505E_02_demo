
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger  # Thêm import này

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

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

app.register_blueprint(api_blueprint, url_prefix='/api')

with app.app_context():
    db.create_all()