from flask import Flask,render_template as rt,request,redirect,url_for,flash
from classes import Person,Admin,Librarian,User
import os
from dotenv import load_dotenv
from db import get_db_connection
import bcrypt
from datetime import datetime
load_dotenv()
app=Flask(__name__) #I'm creating an instance of Flask class
app.secret_key=os.getenv("SECRET_KEY",'thisisasecretkey')

@app.route("/") #listening for root
def home():
    return rt("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        
        pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        if Person.check_user_exists(username, email):
            flash("Username or email already exists")
            return redirect(url_for("register"))
        human=None
        if role == "Admin":
            salary = request.form.get("salary")
            admin_level = request.form.get("admin_level")
            human = Admin(first_name, last_name, username, email, pwd_hash, salary, admin_level)
            
        elif role == "Librarian":
            salary = request.form.get("salary")
            employment_date = request.form.get("employment_date")
            human = Librarian(first_name, last_name, username, email, pwd_hash, salary, employment_date)

        elif role == "User":
            membership_start_date_str = request.form.get("membership_start_date")
            membership_end_date_str = request.form.get("membership_end_date")
            membership_start_date = datetime.strptime(membership_start_date_str, '%Y-%m-%d').date()
            membership_end_date = datetime.strptime(membership_end_date_str, '%Y-%m-%d').date()
            human = User(first_name, last_name, username, email, pwd_hash, membership_start_date, membership_end_date)

        try:
            human.save_to_db()
            flash("User registered successfully")
            return redirect(url_for("login"))
        except ValueError as e:
            flash(str(e))
            return redirect(url_for("register"))

    return rt("register.html")

            
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        q="SELECT * FROM Person WHERE username = %s"
        cursor.execute(q, (username,))
        person = cursor.fetchone()
        conn.close()
        
        if person and bcrypt.checkpw(password.encode('utf-8'), person[5].encode('utf-8')):
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
    return rt('login.html')

if __name__=="__main__":
    app.run(debug=True)