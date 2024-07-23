from enum import Enum
import mysql.connector

class BookType(Enum):
    REGULAR = 'Regular'
    PREMIUM = 'Premium'

class BookState(Enum):
    AVAILABLE = 'Available'
    BORROWED = 'Borrowed'
    LOST = 'Lost'

class Book:
    def __init__(self, title, author, isbn, genre, publication_date, book_type, db_connection):
        self.book_id = None
        self.title = title
        self.author = author
        self.isbn = isbn
        self.genre = genre
        self.publication_date = publication_date
        self.current_state = BookState.AVAILABLE
        self.times_issued = 0
        self.rating = 0.0
        self.book_type = BookType(book_type)
        self.permanent_copies = 1
        self.number_of_borrowed_copies = 0
        self.db_connection = db_connection

    @classmethod
    def from_db_record(cls, record, db_connection):
        book = cls(
            record['Title'],
            record['Author'],
            record['ISBN'],
            record['Genre'],
            record['PublicationDate'],
            record['BookType'],
            db_connection
        )
        book.book_id = record['book_id']
        book.current_state = BookState(record['CurrentState'])
        book.times_issued = record['times_issued']
        book.rating = record['Rating']
        book.permanent_copies = record['NumberOfCopies']
        book.number_of_borrowed_copies = record['NumberOfBorrowedCopies']
        return book

    def add_to_library(self, number_of_copies=1):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO book (Title, Author, ISBN, Genre, PublicationDate, CurrentState, 
                                  times_issued, Rating, BookType, NumberOfCopies, NumberOfBorrowedCopies)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.title, self.author, self.isbn, self.genre, self.publication_date, 
                  self.current_state.value, self.times_issued, self.rating, 
                  self.book_type.value, number_of_copies, self.number_of_borrowed_copies))
            self.db_connection.commit()
            self.book_id = cursor.lastrowid
            self.permanent_copies = number_of_copies
            return True, "Book added to library successfully."
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            return False, f"An error occurred: {str(err)}"
        finally:
            cursor.close()

    def add_copies(self, number_of_books_added):
        self.permanent_copies += number_of_books_added
        self.update_state()
    
    def borrow(self):
        if self.current_state == BookState.AVAILABLE:
            self.number_of_borrowed_copies += 1
            self.times_issued += 1
            self.update_state()
            return True
        else:
            return False
    
    def return_book(self):
        if self.number_of_borrowed_copies > 0:
            self.number_of_borrowed_copies -= 1
            self.update_state()
            return True
        else:
            return False

    def update_state(self):
        if self.number_of_borrowed_copies < self.permanent_copies:
            new_state = BookState.AVAILABLE
        else:
            new_state = BookState.BORROWED
        
        if new_state != self.current_state:
            self.current_state = new_state
        self._update_db_state()

    def _update_db_state(self):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("""
                UPDATE book 
                SET CurrentState = %s, 
                    NumberOfBorrowedCopies = %s,
                    times_issued = %s,
                    NumberOfCopies = %s
                WHERE book_id = %s
            """, (self.current_state.value, self.number_of_borrowed_copies, 
                  self.times_issued, self.permanent_copies, self.book_id))
            self.db_connection.commit()
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            print(f"An error occurred: {str(err)}")
        finally:
            cursor.close()