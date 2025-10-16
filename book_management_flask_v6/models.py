from . import db
from datetime import datetime

class BookTitle(db.Model):
    __tablename__ = 'book_title'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    publisher = db.Column(db.String(100))
    year = db.Column(db.Integer)
    category = db.Column(db.String(100))

    # Quan hệ 1-n với BookCopy
    copies = db.relationship('BookCopy', backref='book_title', lazy=True)

    def __repr__(self):
        return f"<BookTitle {self.title} by {self.author}>"


class BookCopy(db.Model):
    __tablename__ = 'book_copy'

    id = db.Column(db.Integer, primary_key=True)
    book_title_id = db.Column(db.Integer, db.ForeignKey('book_title.id'), nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    available = db.Column(db.Boolean, default=True)
    condition = db.Column(db.String(100), default='Good')  # Good / Damaged / Lost

    # Quan hệ 1-n với Borrowing
    borrowings = db.relationship('Borrowing', backref='book_copy', lazy=True)

    def __repr__(self):
        return f"<BookCopy {self.barcode} ({'Available' if self.available else 'Borrowed'})>"


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    # Quan hệ 1-n với Borrowing
    borrowings = db.relationship('Borrowing', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.name} ({self.email})>"

class Borrowing(db.Model):
    __tablename__ = 'borrowing'

    id = db.Column(db.Integer, primary_key=True)
    book_copy_id = db.Column(db.Integer, db.ForeignKey('book_copy.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    return_date = db.Column(db.DateTime, nullable=True)
    fine = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<Borrowing User:{self.user_id} BookCopy:{self.book_copy_id}>"

