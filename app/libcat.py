# app/libcat.py
import mysql.connector
from models.book import Book, BookType, BookState

class LibCat:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def add_new_book(self, book, number_of_books_added):
        cursor = self.db_connection.cursor()
        try:
            # Check if book already exists
            cursor.execute("SELECT * FROM book WHERE ISBN = %s", (book.isbn,))
            result = cursor.fetchone()

            if result:
                # Update existing book's number of copies
                book.add_copies(number_of_books_added)
                cursor.execute("UPDATE book SET NumberOfCopies = %s, CurrentState = %s WHERE ISBN = %s", 
                               (book.permanent_copies, book.current_state.value, book.isbn,))
            else:
                # Insert new book
                book.add_copies(number_of_books_added - 1)  # add_copies already adds 1, subtracting initial 1
                cursor.execute("""
                    INSERT INTO book (Title, Author, ISBN, Genre, PublicationDate, CurrentState, BookType, NumberOfCopies)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (book.title, book.author, book.isbn, book.genre, book.publication_date, book.current_state.value, book.book_type.value, book.permanent_copies))
                
            self.db_connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.db_connection.rollback()
            raise
        finally:
            cursor.close()

    def delete_book(self, book):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("DELETE FROM book WHERE ISBN = %s", (book.isbn,))
            self.db_connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.db_connection.rollback()
            raise
        finally:
            cursor.close()

    def borrow_book(self, book):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("SELECT NumberOfCopies, NumberOfBorrowedCopies FROM book WHERE ISBN = %s", (book.isbn,))
            result = cursor.fetchone()
            if result and result[0] > result[1]:
                book.borrow()
                cursor.execute("UPDATE book SET NumberOfBorrowedCopies = %s, CurrentState = %s WHERE ISBN = %s", 
                               (book.number_of_borrowed_copies, book.current_state.value, book.isbn,))
                self.db_connection.commit()
            else:
                print(f"Warning: Book with ISBN {book.isbn} is not available for borrowing.")
                raise ValueError(f"Book with ISBN {book.isbn} is not available for borrowing.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.db_connection.rollback()
            raise
        finally:
            cursor.close()

    def return_book(self, book):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("SELECT NumberOfBorrowedCopies FROM book WHERE ISBN = %s", (book.isbn,))
            result = cursor.fetchone()
            if result and result[0] > 0:
                book.return_book()
                cursor.execute("UPDATE book SET NumberOfBorrowedCopies = %s, CurrentState = %s WHERE ISBN = %s", 
                               (book.number_of_borrowed_copies, book.current_state.value, book.isbn,))
                self.db_connection.commit()
            else:
                print(f"Warning: No borrowed copies of the book with ISBN {book.isbn} to return.")
                raise ValueError(f"No borrowed copies of the book with ISBN {book.isbn} to return.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.db_connection.rollback()
            raise
        finally:
            cursor.close()

    def view_book_details(self, isbn):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("SELECT * FROM book WHERE ISBN = %s", (isbn,))
            book_details = cursor.fetchone()
            if book_details:
                return {
                    'BookID': book_details[0],
                    'Title': book_details[1],
                    'Author': book_details[2],
                    'ISBN': book_details[3],
                    'Genre': book_details[4],
                    'PublicationDate': book_details[5],
                    'AvailableCopies': book_details[6] - book_details[7],
                    'CurrentState': BookState.AVAILABLE if book_details[6] > book_details[7] else BookState.BORROWED,
                    'BookType': book_details[8]
                }
            else:
                print(f"Warning: Book with ISBN {isbn} not found.")
                raise ValueError(f"Book with ISBN {isbn} not found.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            raise
        finally:
            cursor.close()