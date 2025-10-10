# library_app/api.py (file mới)
from flask import Blueprint, jsonify, request, abort
from . import db
from .models import Book, User, Borrowing
from datetime import datetime
from flasgger import swag_from  # Để annotate docs

api = Blueprint('api', __name__)

# API cho Books (CRUD)
@api.route('api/v1/books', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'List of books',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'title': {'type': 'string'},
                        'author': {'type': 'string'},
                        'available': {'type': 'boolean'}
                    }
                }
            }
        }
    }
})
def get_books():
    books = Book.query.all()
    return jsonify([{'id': b.id, 'title': b.title, 'author': b.author, 'available': b.available} for b in books])

@api.route('api/v1/books', methods=['POST'])
@swag_from({
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'author': {'type': 'string'}
            },
            'required': ['title', 'author']
        }
    }],
    'responses': {201: {'description': 'Book created'}}
})
def add_book():
    data = request.json
    if not data or not 'title' in data or not 'author' in data:
        abort(400)
    new_book = Book(title=data['title'], author=data['author'])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'message': 'Book added'}), 201

@api.route('api/v1/books/<int:id>', methods=['PUT'])
@swag_from({
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'author': {'type': 'string'}
            }
        }
    }],
    'responses': {200: {'description': 'Book updated'}}
})
def update_book(id):
    book = Book.query.get_or_404(id)
    data = request.json
    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    db.session.commit()
    return jsonify({'message': 'Book updated'})

@api.route('api/v1/books/<int:id>', methods=['DELETE'])
@swag_from({
    'responses': {200: {'description': 'Book deleted'}}
})
def delete_book(id):
    book = Book.query.get_or_404(id)
    if not book.available:
        abort(400, description='Cannot delete borrowed book')
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted'})

# API cho Users (tương tự, CRUD)
@api.route('api/v1/users', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'List of users',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'email': {'type': 'string'}
                    }
                }
            }
        }
    }
})
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name, 'email': u.email} for u in users])

@api.route('api/v1/users', methods=['POST'])
@swag_from({
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'email': {'type': 'string'}
            },
            'required': ['name', 'email']
        }
    }],
    'responses': {201: {'description': 'User created'}}
})
def add_user():
    data = request.json
    if not data or not 'name' in data or not 'email' in data:
        abort(400)
    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User added'}), 201

@api.route('api/v1/users/<int:id>', methods=['PUT'])
@swag_from({
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'email': {'type': 'string'}
            }
        }
    }],
    'responses': {200: {'description': 'User updated'}}
})
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.json
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    db.session.commit()
    return jsonify({'message': 'User updated'})

@api.route('api/v1/users/<int:id>', methods=['DELETE'])
@swag_from({
    'responses': {200: {'description': 'User deleted'}}
})
def delete_user(id):
    user = User.query.get_or_404(id)
    active_borrowings = Borrowing.query.filter_by(user_id=id, return_date=None).count()
    if active_borrowings > 0:
        abort(400, description='Cannot delete user with active borrowings')
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})

# API cho Borrowings
@api.route('api/v1/borrowings', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'List of borrowings',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'book_id': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'borrow_date': {'type': 'string'},
                        'return_date': {'type': 'string'}
                    }
                }
            }
        }
    }
})
def get_borrowings():
    borrowings = Borrowing.query.all()
    return jsonify([{
        'id': b.id,
        'book_id': b.book_id,
        'user_id': b.user_id,
        'borrow_date': b.borrow_date.isoformat(),
        'return_date': b.return_date.isoformat() if b.return_date else None
    } for b in borrowings])

@api.route('api/v1/borrowings', methods=['POST'])
@swag_from({
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'book_id': {'type': 'integer'},
                'user_id': {'type': 'integer'}
            },
            'required': ['book_id', 'user_id']
        }
    }],
    'responses': {201: {'description': 'Book borrowed'}}
})
def borrow_book():
    data = request.json
    if not data or not 'book_id' in data or not 'user_id' in data:
        abort(400)
    book = Book.query.get_or_404(data['book_id'])
    if not book.available:
        abort(400, description='Book not available')
    new_borrowing = Borrowing(book_id=data['book_id'], user_id=data['user_id'])
    book.available = False
    db.session.add(new_borrowing)
    db.session.commit()
    return jsonify({'message': 'Book borrowed'}), 201

@api.route('api/v1/borrowings/<int:id>/return', methods=['POST'])
@swag_from({
    'responses': {200: {'description': 'Book returned'}}
})
def return_book(id):
    borrowing = Borrowing.query.get_or_404(id)
    if borrowing.return_date:
        abort(400, description='Already returned')
    borrowing.return_date = datetime.utcnow()
    book = Book.query.get(borrowing.book_id)
    book.available = True
    db.session.commit()
    return jsonify({'message': 'Book returned'})

# Lấy chi tiết Book theo id
@api.route('api/v1/books/<int:id>', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Book detail',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'title': {'type': 'string'},
                    'author': {'type': 'string'},
                    'available': {'type': 'boolean'}
                }
            }
        },
        404: {'description': 'Book not found'}
    }
})
def get_book(id):
    book = Book.query.get_or_404(id)
    return jsonify({'id': book.id, 'title': book.title, 'author': book.author, 'available': book.available})


# Lấy chi tiết User theo id
@api.route('api/v1/users/<int:id>', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'User detail',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'email': {'type': 'string'}
                }
            }
        },
        404: {'description': 'User not found'}
    }
})
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email})


# Lấy chi tiết Borrowing theo id
@api.route('api/v1/borrowings/<int:id>', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Borrowing detail',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'book_id': {'type': 'integer'},
                    'user_id': {'type': 'integer'},
                    'borrow_date': {'type': 'string'},
                    'return_date': {'type': 'string'}
                }
            }
        },
        404: {'description': 'Borrowing not found'}
    }
})
def get_borrowing(id):
    borrowing = Borrowing.query.get_or_404(id)
    return jsonify({
        'id': borrowing.id,
        'book_id': borrowing.book_id,
        'user_id': borrowing.user_id,
        'borrow_date': borrowing.borrow_date.isoformat(),
        'return_date': borrowing.return_date.isoformat() if borrowing.return_date else None
    })
