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
        self.permanent_copies = 1
        self.Number_of_Borrowed_Copies = 0

    def __hash__(self):
        return hash(self.isbn)

    def __eq__(self, other):
        return self.isbn == other.isbn
    
    def add_copies(self, number_of_books_added):
        self.permanent_copies += number_of_books_added
        self.update_state()
    
    def borrow(self):
        if self.current_state == BookState.AVAILABLE:
            self.number_of_borrowed_copies += 1
            self.times_issued += 1
            self.update_state()
        else:
            raise ValueError("Book is not available for borrowing.")
    
    def return_book(self):
        if self.number_of_borrowed_copies > 0:
            self.number_of_borrowed_copies -= 1
            self.update_state()
        else:
            raise ValueError("No borrowed copies to return.")

    def update_state(self):
        if self.number_of_borrowed_copies < self.permanent_copies:
            self.current_state = BookState.AVAILABLE
        else:
            self.current_state = BookState.BORROWED
        
