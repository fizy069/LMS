from enum import Enum

class BookType(Enum):
    REGULAR = 'Regular'
    PREMIUM = 'Premium'

class BookState(Enum):
    AVAILABLE = 'Available'
    BORROWED = 'Borrowed'
    LOST = 'Lost'

class Book:
    def __init__(self, book_id, title, author, isbn, genre, publication_date, book_type):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.genre = genre
        self.publication_date = publication_date
        self.current_state = BookState.AVAILABLE
        self.book_type = book_type
        self.times_issued = 0
        self.rating = 0.0
        self.copies_available = 1

    def __hash__(self):
        return hash(self.isbn)

    def __eq__(self, other):
        return self.isbn == other.isbn
