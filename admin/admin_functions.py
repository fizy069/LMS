import logging
from datetime import datetime, timedelta
import random
from flask import flash
from db import get_db_connection
from BookCatalog.libcat import LibCat
from BookCatalog.book import Book
class AdminFunctions:
    def __init__(self):
        self.db_connection = get_db_connection()
        self.libcat = LibCat(self.db_connection)
    def check_premium_requests(self):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            q="""
            SELECT UpgradeRequest.request_id, UpgradeRequest.user_id, Person.username, UpgradeRequest.status 
            FROM UpgradeRequest 
            JOIN Person ON UpgradeRequest.user_id = Person.person_id 
            WHERE UpgradeRequest.status = 'Pending'
            """
            cursor.execute(q)
            results = cursor.fetchall()
            logging.debug(f"Query executed: {q}")
            logging.debug(f"Results: {results}")
            if not results:
                return False, "No pending upgrade requests."
            else:
                return results
        except Exception as e:
            logging.error(f"Error in check_premium_requests: {str(e)}")
            return False, str(e)
        finally:
            cursor.close()
    def update_request(self, request_id, status):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("UPDATE UpgradeRequest SET status = %s WHERE request_id = %s", (status, request_id))
            if status=="Approved":
                q="UPDATE User SET membership_type = 'Premium' WHERE user_id=(SELECT user_id FROM UpgradeRequest WHERE request_id=%s)"
                cursor.execute(q, (request_id,))
            q="DELETE FROM UpgradeRequest WHERE request_id=%s"
            cursor.execute(q, (request_id,))
            self.db_connection.commit()
            return True, f"Premium request {request_id} has been {status}."
        except Exception as e:
            self.db_connection.rollback()
            return False, str(e)
        finally:
            cursor.close()
    def check_purchase_orders(self):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM purchase_orders WHERE status = 'Pending'")
            results = cursor.fetchall()
            if not results:
                return False, "No pending purchase orders."
            else:
                return results
        except Exception as e:
            return False, str(e)
        finally:
            cursor.close()
    def generate_unique_isbn(self):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT MAX(isbn) as max_isbn FROM book")
            max_isbn = cursor.fetchone()['max_isbn']
            if not max_isbn:
                max_isbn = 1000000000000
            return str(int(max_isbn) + 1)
        except Exception as e:
            logging.error(f"Error generating unique ISBN: {str(e)}")
            return None
        finally:
            cursor.close()

    def update_purchase_order(self, order_id, status):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            if status=="Approved":
                cursor.execute("select * from purchase_orders where order_id=%s", (order_id,))
                order=cursor.fetchone()
                if order:
                    isbn=self.generate_unique_isbn()
                    if not isbn:
                        raise Exception("Error generating ISBN")
                    
                    today = datetime.today()
                    years_ago = today.replace(year=today.year - 76)
                    if years_ago.month > 2:
                        months_ago = years_ago.replace(month=years_ago.month - 2)
                    else:
                        months_ago = years_ago.replace(month=years_ago.month + 10, year=years_ago.year - 1)
                    publication_date = months_ago - timedelta(days=13)
                    genres = ["Fantasy", "Romance", "Science Fiction", "Mystery", "Thriller", "Non-Fiction", "Historical", "Adventure"]
                    genre = random.choice(genres)
                    new_book = Book(
                        title=order['book_title'],
                        author=order['author'],
                        isbn=isbn,
                        genre=genre,
                        publication_date=publication_date,
                        book_type="Regular",
                        db_connection=self.db_connection
                    )
                    success, message = new_book.add_to_library(order['quantity'])
                    if not success:
                        raise Exception(message)
            cursor.execute("UPDATE purchase_orders SET status = %s WHERE order_id = %s", (status, order_id))
            self.db_connection.commit()
            return True, f"Purchase order {order_id} has been {status}."
        except Exception as e:
            self.db_connection.rollback()
            return False, str(e)
        finally:
            cursor.close()

    def search_users_or_librarians(self, search_term):
        return self.libcat.search_users(search_term)

    def get_overdue_books(self):
        cursor=self.db_connection.cursor(dictionary=True)
        try:
            libcat=LibCat(self.db_connection)
            results=libcat.get_overdue_books()
            '''
            q="""
            SELECT book.book_id,Person.username,book.Title,borrowed_books.due_date from borrowed_books JOIN Person ON borrowed_books.user_id = Person.person_id JOIN book ON borrowed_books.book_id = book.book_id WHERE borrowed_books.due_date < CURDATE()"""
            cursor.execute(q)
            results=cursor.fetchall()
            logging.debug(f"Query executed: {q}")
            logging.debug(f"Results: {results}")
            '''
            if not results:
                return False, "No overdue books."
            else:
                return results
        except Exception as e:
            logging.error(f"Error in get_overdue_books: {str(e)}")
            return False, str(e)
        finally:
            cursor.close()

    def send_warning(self, username, book_title, due_date):
        # for now this just prints the message on the admin screen but it should actually sent an email to 'user_email'
        flash(f"Warning to {username}: The book '{book_title}' was due on {due_date}. Please return it ASAP.")
        return True, f"Warning sent to {username}"

    def get_library_funds(self):
        # fixed for now since we didn't handle revenue part
        return 10000.00

    def mark_book_as_lost(self, book_id):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("select NumberOfCopies from book where book_id=%s", (book_id,))
            result=cursor.fetchone()
            if not result:
                return False, f"Book with id {book_id} not found"
            num_copies=result[0]
            if num_copies>1:
                cursor.execute("UPDATE book SET NumberOfCopies=NumberOfCopies-1 WHERE book_id=%s", (book_id,))
                self.db_connection.commit()
                cursor.execute("DELETE FROM borrowed_books WHERE book_id = %s", (book_id,))
                self.db_connection.commit()
                return True, f"a copy of the Book with id {book_id} is lost"
            elif num_copies==1:
                cursor.execute("update book set NumberOfCopies=0,CurrentState='Lost' where book_id=%s", (book_id,))
                self.db_connection.commit()
                cursor.execute("DELETE FROM borrowed_books WHERE book_id = %s", (book_id,))
                self.db_connection.commit()
                return True, f"Last copy of Book with id {book_id} is lost"
            else:
                
                return False, f"Book with id {book_id} not found, number of copies is {num_copies} num_copies<1"
        except Exception as e:
            self.db_connection.rollback()
            return False, str(e)
        finally:
            cursor.close()
    
    def check_catalog(self):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT book_id,Title,Author,Genre,CurrentState,BookType,NumberOfCopies,NumberOfBorrowedCopies FROM book")
            results = cursor.fetchall()
            if not results:
                return False, "No books in the catalog."
            else:
                return results
        except Exception as e:
            return False, str(e)
        finally:
            cursor.close()
            
    def delete_book(self, book_id):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("SELECT NumberOfBorrowedCopies FROM book WHERE book_id = %s", (book_id,))
            result = cursor.fetchone()
            if not result:
                return False, f"Book with id {book_id} not found."
            num_borrowed_copies = result[0]
            if num_borrowed_copies > 0:
                return False, f"Book with id {book_id} has {num_borrowed_copies} borrowed copies, Cannot Delete it."
            cursor.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
            self.db_connection.commit()
            return True, f"Book with id {book_id} has been deleted."
        except Exception as e:
            self.db_connection.rollback()
            return False, str(e)
        finally:
            cursor.close()
    def __del__(self):
        if self.db_connection:
            self.db_connection.close()