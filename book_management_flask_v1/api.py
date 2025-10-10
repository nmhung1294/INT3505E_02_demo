# library_app/api.py (file mới)
from flask import Blueprint, jsonify, request, abort
from . import db
from .models import Book, User, Borrowing
from datetime import datetime
from flasgger import swag_from  # Để annotate docs

api = Blueprint('api', __name__)

class BookDemo:
    def __init__(self, id, title, author, available):
        self.id = id
        self.title = title
        self.author = author
        self.available = available
        

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
    books = [
        BookDemo(1, "Clean Code", "Robert C. Martin", True),
        BookDemo(2, "The Pragmatic Programmer", "Andrew Hunt", False),
        BookDemo(3, "Introduction to Algorithms", "Thomas H. Cormen", True)
    ]
    return jsonify([
        {'id': b.id, 'title': b.title, 'author': b.author, 'available': b.available}
        for b in books
    ])