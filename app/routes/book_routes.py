from flask import Blueprint, request, jsonify, current_app
from ..models.book import Book, BookType
from ..libcat import LibCat

bp = Blueprint('book_routes', __name__)

@bp.route('/')
def index():
    return "Welcome to the Library Management System"

@bp.route('/add_book', methods=['POST'])
def add_book():
    data = request.json
    book = Book(
        book_id=None,
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        genre=data['genre'],
        publication_date=data['publication_date'],
        book_type=BookType[data['book_type'].upper()]
    )
    libcat = LibCat(current_app.config['DB_CONNECTION'])
    libcat.add_new_book(book)
    return jsonify({"message": "Book added successfully"}), 201

@bp.route('/delete_book', methods=['DELETE'])
def delete_book():
    data = request.json
    book = Book(
        book_id=None,
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        genre=data['genre'],
        publication_date=data['publication_date'],
        book_type=BookType[data['book_type'].upper()]
    )
    libcat = LibCat(current_app.config['DB_CONNECTION'])
    libcat.delete_book(book)
    return jsonify({"message": "Book deleted successfully"}), 200

@bp.route('/borrow_book', methods=['POST'])
def borrow_book():
    data = request.json
    book = Book(
        book_id=None,
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        genre=data['genre'],
        publication_date=data['publication_date'],
        book_type=BookType[data['book_type'].upper()]
    )
    libcat = LibCat(current_app.config['DB_CONNECTION'])
    libcat.borrow_book(book)
    return jsonify({"message": "Book borrowed successfully"}), 200

@bp.route('/return_book', methods=['POST'])
def return_book():
    data = request.json
    book = Book(
        book_id=None,
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        genre=data['genre'],
        publication_date=data['publication_date'],
        book_type=BookType[data['book_type'].upper()]
    )
    libcat = LibCat(current_app.config['DB_CONNECTION'])
    libcat.return_book(book)
    return jsonify({"message": "Book returned successfully"}), 200

@bp.route('/view_book', methods=['GET'])
def view_book():
    data = request.json
    book = Book(
        book_id=None,
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        genre=data['genre'],
        publication_date=data['publication_date'],
        book_type=BookType[data['book_type'].upper()]
    )
    libcat = LibCat(current_app.config['DB_CONNECTION'])
    book_details = libcat.view_book_details(book)
    return jsonify(book_details), 200
