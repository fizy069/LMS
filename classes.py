from datetime import datetime
from db import get_db_connection #we can also directly use it in app.py or wherever we need it rather than using it here.
import bcrypt

class Person:
    def __init__(self,first_name,last_name,username,email,password_hash,role):
        self.first_name=first_name
        self.last_name=last_name
        self.username=username
        self.email=email
        self.password_hash=password_hash
        self.role=self.validate_role(role)
        self.created_at=datetime.now()
        self.updated_at=datetime.now()
        self.person_id=None
    def validate_role(self,role):
        valid_roles=['Admin','Librarian','User']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Role must be one of {valid_roles}.")
        return role
    def save_to_db(self):
        connection=get_db_connection()
        cursor=connection.cursor()
        query="""insert into Person(first_name,last_name,username,email,password_hash,role,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s,%s)"""
        values=(self.first_name,self.last_name,self.username,self.email,self.password_hash,self.role,self.created_at,self.updated_at)
        cursor.execute(query,values) #this ensures that injection attacks are prevented
        connection.commit()
        self.person_id=cursor.lastrowid
        cursor.close()
        connection.close()
    @staticmethod
    def check_user_exists(username, email):
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM Person WHERE username = %s OR email = %s", (username, email))
        result = cur.fetchone()[0]>0
        cur.close()
        con.close()
        return result 

class Admin(Person):
    def __init__(self,first_name,last_name,username,email,password_hash,salary,admin_level):
        super().__init__(first_name,last_name,username,email,password_hash,'Admin')
        self.salary=salary
        self.admin_level=self.validate_admin_level(admin_level)
    def validate_admin_level(self,admin_level):
        lvls=['Super Admin', 'System Admin', 'Library Manager', 'Department Head', 'Admin Assistant']
        if admin_level not in lvls:
            raise ValueError(f"Invalid admin level. Admin level must be one of {lvls}.")
        return admin_level
    def save_to_db(self):
        super().save_to_db()
        con=get_db_connection()
        cur=con.cursor()
        q="insert into Admin (admin_id,salary,admin_level) values(%s,%s,%s)"
        v=(self.person_id,self.salary,self.admin_level)
        cur.execute(q,v)
        con.commit()
        cur.close()
        con.close()
class Librarian(Person):
    def __init__(self,first_name,last_name,username,email,password_hash,salary,employment_date):
        super().__init__(first_name,last_name,username,email,password_hash,'Librarian')
        self.salary=salary
        self.employment_date=employment_date
    def save_to_db(self):
        super().save_to_db()
        con=get_db_connection()
        cur=con.cursor()
        q="insert into librarian (librarian_id,salary,employment_date) values(%s,%s,%s)"
        v=(self.person_id,self.salary,self.employment_date)
        cur.execute(q,v)
        con.commit()
        cur.close()
        con.close()
class User(Person):
    def __init__(self,first_name,last_name,username,email,password_hash,membership_start_date,membership_end_date=None,membership_type='Regular'):
        super().__init__(first_name,last_name,username,email,password_hash,'User')
        self.membership_start_date=membership_start_date or datetime.now().date()
        self.membership_end_date=membership_end_date or datetime(9999, 12, 31).date()
        self.membership_type=self.validate_membership_type(self.determine_membership_type())
    def validate_membership_type(self,membership_type):
        types=['Regular', 'Premium']
        if membership_type not in types:
            raise ValueError(f"Invalid membership type. Membership type must be one of {types}.")
        return membership_type
    def determine_membership_type(self):
        current_date = datetime.now().date()
        if self.membership_start_date <= current_date <= self.membership_end_date:
            return 'Premium'
        else:
            return 'Regular'
    def save_to_db(self):
        super().save_to_db()
        con=get_db_connection()
        cur=con.cursor()
        q="insert into User (user_id,membership_start_date,membership_end_date,membership_type) values(%s,%s,%s,%s)"
        v=(self.person_id,self.membership_start_date,self.membership_end_date,self.membership_type)
        cur.execute(q,v)
        con.commit()
        cur.close()
        con.close()
        
        