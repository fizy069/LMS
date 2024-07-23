from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from db import get_db_connection
from admin.admin_functions import AdminFunctions

admin_bp = Blueprint('admin', __name__, template_folder='templates')
admin_functions = AdminFunctions()

adm_id=None

@admin_bp.route("/admin_home/<int:admin_id>")
def admin_home(admin_id):
    global adm_id
    adm_id=admin_id
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    q = "SELECT * FROM Admin WHERE admin_id = %s"
    cursor.execute(q, (admin_id,))
    admin = cursor.fetchone()
    q="SELECT * FROM Person WHERE person_id=%s"
    cursor.execute(q,(admin_id,))
    person=cursor.fetchone()
    conn.close()
    if admin:
        funds=admin_functions.get_library_funds()
        return render_template('admin_home.html', admin=admin,funds=funds,person=person)
    else:
        flash('Person not in database!')
        return redirect(url_for('login'))

@admin_bp.route("/admin_home/purchase_orders")
def purchase_orders():
    global adm_id
    if adm_id is None:
        flash("Admin ID is not set. Please login again.", 'danger')
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    result = admin_functions.check_purchase_orders()
    
    if isinstance(result, tuple):  # This means an error occurred
        flash(result[1], 'danger')
        orders = []
    else:
        orders = result
    per_page = 5
    total_pages = (len(orders) - 1) // per_page + 1
    start = (page - 1) * per_page
    end = start + per_page
    paginated_orders = orders[start:end]
    
    return render_template('purchase_orders.html', orders=paginated_orders, current_page=page, total_pages=total_pages,admin_id=adm_id)

@admin_bp.route("/admin_home/update_order", methods=['POST'])
def update_order():
    order_id = request.form.get('order_id')
    status = request.form.get('status')
    success, message = admin_functions.update_purchase_order(order_id, status)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.purchase_orders'))

@admin_bp.route("/admin_home/search_users")
def search_users():
    global adm_id
    if adm_id is None:
        flash("Admin ID is not set. Please login again.", 'danger')
        return redirect(url_for('login'))
    search_term = request.args.get('search', '')
    results = admin_functions.search_users_or_librarians(search_term)
    return render_template('search_results.html', results=results,admin_id=adm_id)

@admin_bp.route("/admin_home/overdue_books")
def overdue_books():
    global adm_id
    if adm_id is None:
        flash("Admin ID is not set. Please login again.", 'danger')
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    result = admin_functions.get_overdue_books()
    
    if isinstance(result, tuple):  # This means an error occurred
        flash(result[1], 'danger')
        overdue_books = []
    else:
        overdue_books = result
    per_page = 5
    total_pages = (len(overdue_books) - 1) // per_page + 1
    start = (page - 1) * per_page
    end = start + per_page
    paginated_overdue_books = overdue_books[start:end]
    
    return render_template('overdue_books.html', overdue_books=paginated_overdue_books, current_page=page, total_pages=total_pages,admin_id=adm_id)

@admin_bp.route("/admin_home/send_warning", methods=['POST'])
def send_warning():
    username = request.form.get('username')
    book_title = request.form.get('book_title')
    due_date = request.form.get('due_date')
    success, message = admin_functions.send_warning(username, book_title, due_date)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin.overdue_books'))

@admin_bp.route("/admin_home/mark_lost", methods=['POST'])
def mark_lost():
    book_id = request.form.get('book_id')
    success, message = admin_functions.mark_book_as_lost(book_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin.overdue_books'))

@admin_bp.route("/admin_home/premium_requests", methods=['GET', 'POST'])
def premium_requests():
    global adm_id
    if adm_id is None:
        flash("Admin ID is not set. Please login again.", 'danger')
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    result = admin_functions.check_premium_requests()
    
    if isinstance(result, tuple) and result[0] is False:  # error
        flash(result[1], 'danger')
        requests = []
        total_pages = 1
    else:
        requests = result
        per_page = 5
        total_pages = (len(requests) - 1) // per_page + 1
        start = (page - 1) * per_page
        end = start + per_page
        requests = requests[start:end]
    
    return render_template('upgrade_requests.html', requests=requests, current_page=page, total_pages=total_pages,admin_id=adm_id)
@admin_bp.route("/admin_home/update_requests", methods=['POST'])
def update_requests():
    request_id = request.form.get('request_id')
    status = request.form.get('status')
    success, message = admin_functions.update_request(request_id, status)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.premium_requests'))

@admin_bp.route("/admin_home/view_catalog", methods=['GET', 'POST'])
def view_catalog():
    global adm_id
    if adm_id is None:
        flash("Admin ID is not set. Please login again.", 'danger')
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    result = admin_functions.check_catalog()
    
    if isinstance(result, tuple) and result[0] is False:  # error
        flash(result[1], 'danger')
        books = []
        total_pages = 1
    else:
        books = result
        per_page = 5
        total_pages = (len(books) - 1) // per_page + 1
        start = (page - 1) * per_page
        end = start + per_page
        books = books[start:end]
    
    return render_template('view_catalog.html', books=books, current_page=page, total_pages=total_pages,admin_id=adm_id)

@admin_bp.route("/admin_home/delete_book", methods=['POST'])
def delete_book():
    book_id = request.form.get('book_id')
    success, message = admin_functions.delete_book(book_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.view_catalog'))