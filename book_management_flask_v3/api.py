from flask import Blueprint, jsonify, request, abort
from . import db
from .models import Book, User, Borrowing
from datetime import datetime, timedelta
from flasgger import swag_from
from functools import wraps
import jwt
import os

api = Blueprint('api', __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "nmhung_secret")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Bỏ qua xác thực cho Swagger
        if request.path.startswith("/apidocs") or request.path.startswith("/flasgger_static"):
            return f(*args, **kwargs)

        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@api.route('api/v1/register', methods=['POST'])
@swag_from({
    'summary': 'Đăng ký người dùng mới',
    'description': 'Tạo user mới và tự động trả về JWT token có hiệu lực 1 giờ.',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'example': 'Alice'},
                'email': {'type': 'string', 'example': 'alice@example.com'}
            },
            'required': ['name', 'email']
        }
    }],
    'responses': {
        201: {'description': 'User registered successfully with JWT token'},
        400: {'description': 'Missing fields or email already exists'}
    }
})
def register():
    data = request.json
    if not data or 'name' not in data or 'email' not in data:
        abort(400, description="Name and email required")

    # Kiểm tra email tồn tại
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        abort(400, description="Email already registered")

    # Tạo user mới
    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()

    # Sinh token JWT có hiệu lực 1h
    token = jwt.encode({
        'user_id': new_user.id,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({
        'message': 'User registered successfully',
        'token': token
    }), 201


# ======================================================
# API: Đăng nhập
# ======================================================
@api.route('api/v1/login', methods=['POST'])
@swag_from({
    'summary': 'Đăng nhập người dùng',
    'description': 'Nhập email để lấy JWT token hợp lệ trong 1 giờ.',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'example': 'alice@example.com'}
            },
            'required': ['email']
        }
    }],
    'responses': {
        200: {'description': 'JWT token returned'},
        400: {'description': 'Email required'},
        401: {'description': 'Invalid email'}
    }
})
def login():
    data = request.json
    if not data or 'email' not in data:
        abort(400, description="Email required")

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        abort(401, description="Invalid email")

    # Sinh token JWT
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({'token': token})


# ======================================================
# BOOK APIs
# ======================================================
from flask import Blueprint, jsonify, request, abort
from . import db
from .models import Book, User, Borrowing
from datetime import datetime, timedelta
from functools import wraps
import jwt
import os

api = Blueprint('api', __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "nmhung_secret")

# ===============================
# JWT AUTH DECORATOR
# ===============================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['id'])
            if not current_user:
                raise Exception("Invalid user")
        except Exception as e:
            return jsonify({'message': f'Invalid token: {str(e)}'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


# ===============================
# AUTH APIs
# ===============================
@api.route('/api/v1/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        schema:
          properties:
            name:
              type: string
            email:
              type: string
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing or duplicate email
    """
    data = request.json
    if not data or 'name' not in data or 'email' not in data:
        abort(400, description='Missing name or email')

    if User.query.filter_by(email=data['email']).first():
        abort(400, description='Email already registered')

    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@api.route('/api/v1/login', methods=['POST'])
def login():
    """
    Login user and get JWT token
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        schema:
          properties:
            email:
              type: string
    responses:
      200:
        description: Login success, return JWT token
      401:
        description: Invalid email
    """
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    if not user:
        abort(401, description='Invalid email')

    token = jwt.encode(
        {'id': user.id, 'exp': datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm='HS256'
    )
    return jsonify({'token': token})


# ===============================
# BOOK APIs
# ===============================
@api.route('/api/v1/books', methods=['GET'])
@token_required
def get_books(current_user):
    """
    Get all books
    ---
    tags:
      - Books
    security:
      - Bearer: []
    responses:
      200:
        description: List of all books
    """
    books = Book.query.all()
    return jsonify([
        {'id': b.id, 'title': b.title, 'author': b.author, 'available': b.available}
        for b in books
    ])


@api.route('/api/v1/books', methods=['POST'])
@token_required
def add_book(current_user):
    """
    Add a new book
    ---
    tags:
      - Books
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          properties:
            title:
              type: string
            author:
              type: string
    responses:
      201:
        description: Book added successfully
    """
    data = request.json
    if not data or 'title' not in data or 'author' not in data:
        abort(400)
    new_book = Book(title=data['title'], author=data['author'])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'message': 'Book added'}), 201


@api.route('/api/v1/books/<int:id>', methods=['PUT'])
@token_required
def update_book(current_user, id):
    """
    Update a book
    ---
    tags:
      - Books
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
      - in: body
        name: body
        schema:
          properties:
            title:
              type: string
            author:
              type: string
    responses:
      200:
        description: Book updated successfully
    """
    book = Book.query.get_or_404(id)
    data = request.json or {}
    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    db.session.commit()
    return jsonify({'message': 'Book updated'})


@api.route('/api/v1/books/<int:id>', methods=['DELETE'])
@token_required
def delete_book(current_user, id):
    """
    Delete a book
    ---
    tags:
      - Books
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
    responses:
      200:
        description: Book deleted successfully
    """
    book = Book.query.get_or_404(id)
    if not book.available:
        abort(400, description='Cannot delete borrowed book')
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted'})


@api.route('/api/v1/books/<int:id>', methods=['GET'])
@token_required
def get_book(current_user, id):
    """
    Get book by ID
    ---
    tags:
      - Books
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
    responses:
      200:
        description: Return a single book
    """
    book = Book.query.get_or_404(id)
    return jsonify({'id': book.id, 'title': book.title, 'author': book.author, 'available': book.available})


# ===============================
# USER APIs
# ===============================
@api.route('/api/v1/users', methods=['GET'])
@token_required
def get_users(current_user):
    """
    Get all users
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: List of all users
    """
    users = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name, 'email': u.email} for u in users])


@api.route('/api/v1/users/<int:id>', methods=['GET'])
@token_required
def get_user(current_user, id):
    """
    Get user by ID
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
    responses:
      200:
        description: Return user info
    """
    user = User.query.get_or_404(id)
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email})


# ===============================
# BORROWING APIs
# ===============================
@api.route('/api/v1/borrowings', methods=['GET'])
@token_required
def get_borrowings(current_user):
    """
    Get all borrowings
    ---
    tags:
      - Borrowings
    security:
      - Bearer: []
    responses:
      200:
        description: List of all borrowings
    """
    borrowings = Borrowing.query.all()
    return jsonify([{
        'id': b.id,
        'book_id': b.book_id,
        'user_id': b.user_id,
        'borrow_date': b.borrow_date.isoformat(),
        'return_date': b.return_date.isoformat() if b.return_date else None
    } for b in borrowings])


@api.route('/api/v1/borrowings', methods=['POST'])
@token_required
def borrow_book(current_user):
    """
    Borrow a book
    ---
    tags:
      - Borrowings
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          properties:
            book_id:
              type: integer
            user_id:
              type: integer
    responses:
      201:
        description: Book borrowed successfully
    """
    data = request.json
    if not data or 'book_id' not in data or 'user_id' not in data:
        abort(400)
    book = Book.query.get_or_404(data['book_id'])
    if not book.available:
        abort(400, description='Book not available')
    new_borrowing = Borrowing(book_id=data['book_id'], user_id=data['user_id'])
    book.available = False
    db.session.add(new_borrowing)
    db.session.commit()
    return jsonify({'message': 'Book borrowed'}), 201


@api.route('/api/v1/borrowings/<int:id>/return', methods=['POST'])
@token_required
def return_book(current_user, id):
    """
    Return a borrowed book
    ---
    tags:
      - Borrowings
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
    responses:
      200:
        description: Book returned successfully
    """
    borrowing = Borrowing.query.get_or_404(id)
    if borrowing.return_date:
        abort(400, description='Already returned')
    borrowing.return_date = datetime.utcnow()
    book = Book.query.get(borrowing.book_id)
    book.available = True
    db.session.commit()
    return jsonify({'message': 'Book returned'})
