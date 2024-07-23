import mysql.connector
db_config={
    'host':'localhost',
    'user':'',
    'password':'',
    'database':'library',
}

def get_db_connection():
    connector=mysql.connector.connect(**db_config)
    return connector