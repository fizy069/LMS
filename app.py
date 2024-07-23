from email.mime.text import MIMEText
import random
import smtplib
import string
from flask import Flask,render_template as rt,request,redirect,url_for,flash
from classes import Person,Admin,Librarian,User
import os
from dotenv import load_dotenv
from db import get_db_connection
import bcrypt
from datetime import datetime


from admin.routes import admin_bp
from librarian.routes import librarian_bp
from user.routes import user_bp

load_dotenv()
app=Flask(__name__) #I'm creating an instance of Flask class
app.secret_key=os.getenv("SECRET_KEY",'thisisasecretkey')

app.register_blueprint(admin_bp)
app.register_blueprint(librarian_bp)
app.register_blueprint(user_bp)



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
            if salary=='':
                salary_int=0
            else:
                salary_int=int(salary)
            employment_date = request.form.get("employment_date")
            human = Librarian(first_name, last_name, username, email, pwd_hash, salary_int, employment_date)

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
        cursor = conn.cursor(dictionary=True)
        q="SELECT * FROM Person WHERE username = %s"
        cursor.execute(q, (username,))
        person = cursor.fetchone()
        conn.close()
        
        if person and bcrypt.checkpw(password.encode('utf-8'), person['password_hash'].encode('utf-8')):
            flash('Login successful!')
            return role_spcific_router(person)
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
    return rt('login.html')
def role_spcific_router(person):
    tempRole=person['role']
    if tempRole=='User':
        return redirect(url_for('user.user_home', user_id=person['person_id']))
    elif tempRole=='Admin':
        return redirect(url_for('admin.admin_home', admin_id=person['person_id']))
    elif  tempRole=='Librarian':
        return redirect(url_for('librarian.librarian_home', librarian_id=person['person_id']))

def generateRandomPassword(length=12):
    chars=string.ascii_letters+string.digits+string.punctuation
    return ''.join(random.choice(chars) for i in range(length))
def sendEmail(to,subject,body):
    smtpServer="smtp.gmail.com"
    smtpPort=587
    smtpUsername="LMSProject.BITS@gmail.com"
    smtpPassword="LMSProject5*"
    msg=MIMEText(body)
    msg['Subject']=subject
    msg['From']=smtpUsername
    msg['To']=to
    try:
        with smtplib.SMTP(smtpServer,smtpPort) as server:
            server.starttls()
            server.login(smtpUsername,smtpPassword)
            server.send_message(msg)
        print("Email sent")
    except Exception as e:
        print("Error sending email")
        print(e)
@app.route("/forgot_password",methods=["GET","POST"])
def forgot_password():
    if request.method=="POST":
        email=request.form.get("email")
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)
        q="SELECT * FROM Person WHERE email=%s"
        cursor.execute(q,(email,))
        person=cursor.fetchone()
        if person:
            temp_password=generateRandomPassword()
            temp_password_hash=bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt())
            q="UPDATE Person SET password_hash=%s WHERE email=%s"
            cursor.execute(q,(temp_password_hash,email))
            conn.commit()
            
            #semding mail
            subject="Password Reset"
            body=f"Your new password is {temp_password}\nPlease login and change your password"
            sendEmail(email,subject,body)
            flash("New password has been sent to your email")
            return redirect(url_for("login"))
        else:
            flash("Email not found","error")
        cursor.close()
        conn.close()
    return rt("forgot_password.html")
if __name__=="__main__":
    app.run(debug=True)