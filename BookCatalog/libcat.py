# app/libcat.py
import mysql.connector
from BookCatalog.book import Book, BookType, BookState

class LibCat:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def add_new_book(self, book, number_of_books_added):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM book WHERE ISBN = %s", (book.isbn,))
            result = cursor.fetchone()

            if result:
                existing_book = Book.from_db_record(result, self.db_connection)
                existing_book.add_copies(number_of_books_added)
                return True, "Book updated successfully."
            else:
                success, message = book.add_to_library(number_of_books_added)
                return success, message

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.db_connection.rollback()
            return False, f"An error occurred: {str(err)}"
        finally:
            cursor.close()

    def delete_book(self, isbn):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("DELETE FROM book WHERE ISBN = %s", (isbn,))
            if cursor.rowcount == 0:
                return False, "Book not found."
            self.db_connection.commit()
            return True, "Book deleted successfully."
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.db_connection.rollback()
            return False, f"An error occurred: {str(err)}"
        finally:
            cursor.close()

    def borrow_book(self, book_id, user_id):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM borrowed_books WHERE book_id=%s and user_id=%s",(book_id,user_id,))
            check=cursor.fetchall()
            if check:
                return False,"Book is already borrowed by you."
            
            cursor.execute("SELECT * FROM book WHERE book_id = %s", (book_id,))
            book_data = cursor.fetchone()
            
            if book_data:
                book = Book.from_db_record(book_data, self.db_connection)
                
                if book.borrow():
                    cursor.execute("""
                        INSERT INTO borrowed_books (book_id, user_id, borrow_date, due_date)
                        VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))
                    """, (book_id, user_id))
                    
                    self.db_connection.commit()
                    return True , "Book borrowed successfully."
                else:
                    return False, "Book is not available for borrowing."
            else:
                return False, "Book not found."
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            return False, f"An error occurred: {str(err)}"
        finally:
            cursor.close()

    def return_book(self, book_id, user_id):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM book WHERE book_id = %s", (book_id,))
            book_data = cursor.fetchone()
            
            if book_data:
                book = Book.from_db_record(book_data, self.db_connection)
                
                if book.return_book():
                    cursor.execute("""
                        INSERT INTO borrow_history (book_id, user_id, borrow_date, due_date, return_date)
                        SELECT book_id, user_id, borrow_date, due_date, CURDATE()
                        FROM borrowed_books
                        WHERE book_id = %s AND user_id = %s
                    """, (book_id, user_id))

                    cursor.execute("""
                        DELETE FROM borrowed_books
                        WHERE book_id = %s AND user_id = %s
                    """, (book_id, user_id))

                    self.db_connection.commit()
                    return True, "Book returned successfully."
                else:
                    return False, "Book return failed. It may not be borrowed."
            else:
                return False, "Book not found."
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            return False, f"An error occurred: {str(err)}"
        finally:
            cursor.close()

    def view_book_details(self, isbn):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM book WHERE ISBN = %s", (isbn,))
            book_details = cursor.fetchone()
            if book_details:
                book = Book.from_db_record(book_details, self.db_connection)
                return {
                    'BookID': book.book_id,
                    'Title': book.title,
                    'Author': book.author,
                    'ISBN': book.isbn,
                    'Genre': book.genre,
                    'PublicationDate': book.publication_date,
                    'AvailableCopies': book.permanent_copies - book.number_of_borrowed_copies,
                    'CurrentState': book.current_state,
                    'BookType': book.book_type
                }
            else:
                return None
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
    
    def get_user_details(self, user_id):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Person JOIN User ON Person.person_id = User.user_id WHERE person_id = %s", (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def get_available_books(self):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM book WHERE CurrentState = 'Available'")
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_borrowed_books(self, user_id):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT book.*, borrowed_books.due_date 
                FROM book 
                JOIN borrowed_books ON book.book_id = borrowed_books.book_id 
                WHERE borrowed_books.user_id = %s
            """, (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_borrow_history(self, user_id):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT book.Title, borrow_history.borrow_date, borrow_history.due_date, borrow_history.return_date
                FROM borrow_history
                JOIN book ON borrow_history.book_id = book.book_id
                WHERE borrow_history.user_id = %s
                ORDER BY borrow_history.borrow_date DESC
            """, (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def apply_premium(self, user_id):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("""
                UPDATE User 
                SET membership_type = 'Premium', 
                    membership_end_date = DATE_ADD(CURDATE(), INTERVAL 1 YEAR)
                WHERE user_id = %s
            """, (user_id,))
            self.db_connection.commit()
            return True, "Congratulations! You are now a premium member."
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            return False, f"An error occurred: {str(err)}"
        finally:
            cursor.close()

    def get_all_users(self): ## by email
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT email FROM Person JOIN User ON Person.person_id = User.user_id")
            return cursor.fetchall()
        finally:
            cursor.close()

    def search_users(self, search_term):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT Person.*, User.membership_type, Librarian.employment_date
                FROM Person
                LEFT JOIN User ON Person.person_id = User.user_id
                LEFT JOIN Librarian ON Person.person_id = Librarian.librarian_id
                WHERE Person.username LIKE %s OR Person.email LIKE %s AND Person.role != 'Admin'
            """, (f"%{search_term}%", f"%{search_term}%"))
            return cursor.fetchall()
        finally:
            cursor.close()

    def mark_book_as_lost(self, book_id):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM book WHERE book_id = %s", (book_id,))
            book_data = cursor.fetchone()
            
            if book_data:
                book = Book.from_db_record(book_data, self.db_connection)
                book.current_state = BookState.LOST
                book._update_db_state()
                
                self.db_connection.commit()
                return True, "Book marked as lost."
            else:
                return False, "Book not found."
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            return False, f"An error occurred: {str(err)}"
        finally:
            cursor.close()

    def get_overdue_books(self):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT book.book_id,Person.username, book.Title, borrowed_books.due_date 
                FROM borrowed_books 
                JOIN Person ON borrowed_books.user_id = Person.person_id 
                JOIN book ON borrowed_books.book_id = book.book_id 
                WHERE borrowed_books.due_date < CURDATE()
            """)
            return cursor.fetchall()
        finally:
            cursor.close()