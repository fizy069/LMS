import mysql.connector
db_config={
    'host':'localhost',
    'user':'root',
    'password':'sqlschema01072024',
    'database':'library',
}

def get_db_connection():
    connector=mysql.connector.connect(**db_config)
    return connector