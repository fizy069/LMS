from datetime import date
import re
from flask import render_template as rt, redirect, request, url_for, flash
from flask import Blueprint
from db import get_db_connection
librarian_bp=Blueprint('librarian',__name__,template_folder='templates')


@librarian_bp.route('/librarian_home/<int:librarian_id>', methods=['GET', 'POST'])
def librarian_home(librarian_id):
    con=get_db_connection()
    cur=con.cursor()
    q="SELECT * FROM Person WHERE person_id = %s"
    values=(librarian_id,)
    cur.execute(q,values)
    librarian = cur.fetchone()

    if not librarian:
        flash('Librarian not found!')
        return redirect(url_for('login'))
    #fetching books
    cur.execute("SELECT Title, author, numberofcopies FROM book")
    books = cur.fetchall()
    print(books[0])
    cur.close()
    con.close()    
         
    if request.method == 'POST':
        return place_order(librarian_id)
    
    # Render the librarian homepage template with librarian data
    return rt('librarian_homepage.html', librarian=librarian, librarian_id=librarian_id,books=books)

@librarian_bp.route('/librarian_home/<int:librarian_id>/place_order', methods=['POST'])
def db_insertToPurchaseOrder(librarian_id, book_title, author, quantity):

        con = get_db_connection()
        cur = con.cursor()
        current_date = date.today().isoformat()
        q_insert = "INSERT INTO purchase_orders (librarian_id, book_title, author, quantity, order_date, status) VALUES (%s, %s, %s, %s, %s, 'Pending');"
        values_insert = (librarian_id, book_title, author, quantity, current_date)
        cur.execute(q_insert, values_insert)
        con.commit()
        flash('Order placed successfully!', 'success')
        cur.close()
        con.close()

def place_order(librarian_id):
    if request.method == 'POST':
        book_title = request.form['bookTitle']
        author = request.form['author']
        quantity = request.form['quantity']
        
        # Insert into purchase_orders table
        db_insertToPurchaseOrder(librarian_id, book_title, author, quantity)
        
        print(f"Order placed by Librarian ID {librarian_id}: {quantity} of '{book_title}' by {author}")
        
        return redirect(url_for('librarian.librarian_home', librarian_id=librarian_id))

@librarian_bp.route('/librarian_home/<int:librarian_id>/edit', methods=['POST'])
def update_librarian_profile(librarian_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Retrieve existing librarian profile
    cursor.execute("SELECT * FROM Person WHERE person_id = %s", (librarian_id,))
    librarian = cursor.fetchone()

    if not librarian:
        flash('Librarian not found!', 'error')
        return redirect(url_for('home'))

    if request.method == "POST":
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()

        errors = []

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

        # Check for existing username or email
        cursor.execute("SELECT * FROM Person WHERE (username = %s OR email = %s) AND person_id != %s", (username, email, librarian_id))
        existing_user = cursor.fetchone()
        if existing_user:
            if existing_user['username'] == username:
                errors.append('Username already exists.')
            if existing_user['email'] == email:
                errors.append('Email already exists.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('librarian.edit_librarian_profile', librarian_id=librarian_id))

        # Update the profile if no errors
        update_query = """
        UPDATE Person 
        SET first_name = %s, last_name = %s, email = %s, username = %s, updated_at = %s 
        WHERE person_id = %s
        """
        update_values = (first_name, last_name, email, username, date.today().isoformat(), librarian_id)

        cursor.execute(update_query, update_values)
        conn.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('librarian.librarian_home', librarian_id=librarian_id))

    return redirect(url_for('librarian.librarian_home', librarian_id=librarian_id))

def getPersonByID(librarian_id):
    con=get_db_connection()
    cur=con.cursor()
    q="SELECT * FROM Person WHERE person_id = %s"
    values=(librarian_id,)
    cur.execute(q,values)
    librarian = cur.fetchone()
    cur.close()
    con.close()  
    return librarian

@librarian_bp.route('/librarian_home/<int:librarian_id>/edit', methods=['GET', 'POST'])
def edit_librarian_profile(librarian_id):
    librarian = getPersonByID(librarian_id)
    if not librarian:
        flash('Something went wrong')
        return redirect(url_for('login'))  # Redirect to login if librarian not found
    
    if request.method == 'POST':
        return update_librarian_profile(librarian_id)
        
    
    # Render the edit librarian profile template with librarian data
    return rt('edit_librarian_profile.html', librarian=librarian,librarian_id=librarian_id)

@librarian_bp.route('/librarian_home/<int:librarian_id>/View_borrowed_books')
def View_borrowed_books_home(librarian_id):
    librarian = getPersonByID(librarian_id)
    if not librarian:
        flash('Librarian not found!')
        return redirect(url_for('login'))
    #fetching books
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("""SELECT book.title, book.author, person.first_name, borrowed_books.borrow_date, 
    borrowed_books.due_date from borrowed_books JOIN book ON borrowed_books.book_id = book.book_id 
    JOIN person ON borrowed_books.user_id = person.person_id;""")
    entry = cur.fetchall()
    print(entry[0])
    cur.close()
    con.close()
    return rt('librarian_homepage_borrowed_books.html', librarian=librarian, librarian_id=librarian_id,entry=entry)    