# app/libcat.py
import mysql.connector

class LibCat:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def add_new_book(self, book):
        cursor = self.db_connection.cursor()
        try:
            # Check if book already exists
            cursor.execute("SELECT * FROM book WHERE ISBN = %s", (book.isbn,))
            result = cursor.fetchone()

            if result:
                # Update existing book's number of copies
                cursor.execute("UPDATE book SET NumberOfCopies = NumberOfCopies + 1 WHERE ISBN = %s", (book.isbn,))
            else:
                # Insert new book
                cursor.execute("""
                    INSERT INTO book (Title, Author, ISBN, Genre, PublicationDate, CurrentState, BookType)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (book.title, book.author, book.isbn, book.genre, book.publication_date, book.current_state.value, book.book_type.value))
                
            self.db_connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
