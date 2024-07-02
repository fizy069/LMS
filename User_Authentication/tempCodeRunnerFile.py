@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        person = Person(first_name, last_name, username, email, password, role)
        pwd_hash = person.password_hash
        human=None
        if person.check_user_exists(username, email):
            flash("Username or email already exists")
            return redirect(url_for("register"))
        
        if role == "Admin":
            salary = request.form.get("salary")
            admin_level = request.form.get("admin_level")
            human = Admin(first_name, last_name, username, email, pwd_hash, salary, admin_level)
            
        elif role == "Librarian":
            salary = request.form.get("salary")
            employment_date = request.form.get("employment_date")
            human = Librarian(first_name, last_name, username, email, pwd_hash, salary, employment_date)

        elif role == "User":
            membership_start_date = request.form.get("membership_start_date")
            membership_end_date = request.form.get("membership_end_date")
            human = User(first_name, last_name, username, email, pwd_hash, membership_start_date, membership_end_date)

        try:
            person.save_to_db()
            human.save_to_db()
            flash("User registered successfully")
            return redirect(url_for("login"))
        except ValueError as e:
            flash(str(e))
            return redirect(url_for("register"))

    return rt("register.html")