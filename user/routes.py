from datetime import date, datetime
import re
import bcrypt
from flask import render_template as rt, redirect, request, url_for, flash
from flask import Blueprint
from db import get_db_connection
from BookCatalog.libcat import LibCat
user_bp=Blueprint('user',__name__,template_folder='templates')

@user_bp.route("/user_home/<int:user_id>")
def user_home(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    q = "SELECT * FROM User WHERE user_id = %s"
    cursor.execute(q, (user_id,))
    user = cursor.fetchone()
    q = "SELECT * FROM Person WHERE person_id = %s"
    cursor.execute(q, (user_id,))
    person = cursor.fetchone()
    if not user or not person:
        cursor.close()
        conn.close()
        flash('Person not in database!', 'error')
        return redirect(url_for('login'))
    curr_date = date.today().isoformat()
    q_check_overdue = "SELECT * FROM borrowed_books WHERE user_id = %s AND due_date < %s"
    cursor.execute(q_check_overdue, (user_id, curr_date))
    defaulters = cursor.fetchall()
    cursor.close()
    conn.close()
    if defaulters:
        flash("You have overdue books. Please return them ASAP to prevent any excess charges.", 'error')
    return rt('user_home.html', user=user, person=person)

@user_bp.route("/user_home/request_upgrade",methods=["POST","GET"])
def request_upgrade():
    user_id=None
    if request.method=="POST":
        user_id=request.form.get('user_id')
        conn=get_db_connection()
        cursor=conn.cursor()
        
        qCheckPremium="select membership_type from User where user_id=%s"
        cursor.execute(qCheckPremium,(user_id,))
        membership_type=cursor.fetchone()
        if membership_type and membership_type[0]=='Premium':
            conn.close()
            flash("User is already a premium member!")
            return rt('request_upgrade_failure.html',user_id=user_id)

        qCheck="select * from UpgradeRequest where user_id=%s and status='Pending'"
        cursor.execute(qCheck,(user_id,))
        if cursor.fetchone():
            flash("Upgrade request already sent by you!")
            return rt('request_upgrade_failure.html',user_id=user_id)
        else:
            q="INSERT INTO UpgradeRequest(user_id) values (%s)"
            cursor.execute(q,(user_id,))
            conn.commit()
            conn.close()
            flash("Upgrade request sent to admin!")
            return rt('request_upgrade_success.html',user_id=user_id)
    if user_id is None:
        flash("User ID not provided!!")
        return rt('request_upgrade_failure.html')
    return rt('request_upgrade_success.html',user_id=user_id)

'''
create table UpgradeRequest(request_id int primary key auto_increment, user_id int, status ENUM('Pending','Approved','Rejected') default 'Pending', foreign key(user_id) references User(user_id));
'''
@user_bp.route("/user_home/edit_profile/<int:user_id>", methods=["GET", "POST"])
def edit_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Person WHERE person_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('login'))
        errors = []
        if request.method == "POST":
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            if not first_name:
                errors.append('First name cannot be empty.')
            if not last_name:
                errors.append('Last name cannot be empty.')
            if not email:
                errors.append('Email cannot be empty.')
            if not username:
                errors.append('Username cannot be empty.')
 
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                errors.append('Invalid email format.')
 
            cursor.execute("SELECT * FROM Person WHERE (username = %s OR email = %s) AND person_id != %s", (username, email, user_id))
            existing_user = cursor.fetchone()
            if existing_user:
                if existing_user['username'] == username:
                    errors.append('Username already exists.')
                if existing_user['email'] == email:
                    errors.append('Email already exists.')
 
            if new_password:
                if new_password != confirm_password:
                    errors.append('Passwords do not match.')
                elif len(new_password) < 8:
                    errors.append('Password must be at least 8 characters long.')
 
            if not errors:
                update_query = """
                UPDATE Person 
                SET first_name = %s, last_name = %s, email = %s, username = %s, updated_at = %s
                """
                update_values = [first_name, last_name, email, username, datetime.now()]
 
                if new_password:
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    update_query += ", password_hash = %s"
                    update_values.append(hashed_password)
 
                update_query += " WHERE person_id = %s"
                update_values.append(user_id)
 
                cursor.execute(update_query, tuple(update_values))
                conn.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('user.user_home', user_id=user_id))
            else:
                for error in errors:
                    flash(error, 'error')
 
        return rt('edit_profile.html', user=user)
    
 
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('user.user_home', user_id=user_id))
 
    finally:
        cursor.close()
        conn.close()    
        


@user_bp.route("/user_home/view_borrowed_books",methods=["POST"])
def view_borrowed_books():
    user_id = request.form.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT book_id ,borrow_date, due_date FROM borrowed_books WHERE user_id = %s"
    
    cursor.execute(query, (user_id,))
    b1=cursor.fetchall()
    if  not b1:
        return rt('No_books_Borrowed.html',  user_id=user_id)
        
    borrowed_books = b1
    book_ids = [book[0] for book in borrowed_books]

    query = "SELECT title FROM book WHERE book_id IN (%s)" % ','.join(map(str, book_ids))
    cursor.execute(query)
    titles = cursor.fetchall()

    return rt('view_borrowed_books.html', borrowed_books=borrowed_books, user_id=user_id, titles=titles)


@user_bp.route('/user_home/borrow_book', methods=['GET', 'POST'])
def borrow_book():
    user_id = request.form.get('user_id')
    return rt('borrow_book.html', user_id=user_id)

@user_bp.route('/user_home/search_book', methods=['GET', 'POST'])
def search_book():
    user_id = request.form.get('user_id')
    return rt('search_book.html',user_id=user_id)
        
    
@user_bp.route('/user_home/display_search_results', methods=['POST'])
def display_search_results():
    book_title = request.form['book_title']
    user_id=request.form.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT  title, author, genre, book_id FROM book WHERE title LIKE %s"
    cursor.execute(query, ('%' + book_title + '%',))
    search_results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rt('display_search_results.html', search_results=search_results, book_title=book_title,user_id=user_id)


@user_bp.route('/user_home/borrow_selected_book', methods=['POST'])
def borrow_selected_book():
    user_id = request.form.get('user_id')
    return rt('borrow_selected_book.html',user_id=user_id)

@user_bp.route('/user_home/borrow_book_action', methods=['POST'])
def borrow_book_action():
    book_id = request.form.get('book_id')
    user_id = request.form.get('user_id')
    if not book_id or not user_id:
        return "Book ID not provided", 400
    conn = get_db_connection()
    libcat = LibCat(conn)
    try:
        success, message = libcat.borrow_book(book_id, user_id)
        if success:
            return rt('borrow_success.html', message=message, user_id=user_id)
        else:
            return rt('borrow_failure.html', message=message, user_id=user_id)
    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500
    finally:
        conn.close()
        
        
@user_bp.route('/return_book', methods=['GET', 'POST'])
def return_book():
    user_id = request.form.get('user_id')
    return rt('return_book.html',user_id=user_id)        
 
@user_bp.route('/user_home/return_book_action', methods=['POST'])
def return_book_action():
    book_id = request.form.get('book_id')
    user_id = request.form.get('user_id')

    if not book_id or not user_id:
        return "Book ID not provided", 400

    conn = get_db_connection()
    libcat = LibCat(conn)

    try:
        success, message = libcat.return_book(book_id, user_id)
        if success:
            return rt('return_success.html', message=message, user_id=user_id)
        else:
            return rt('return_failure.html', message=message, user_id=user_id)
    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500
    finally:
        conn.close()