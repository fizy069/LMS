from flask import Flask
import mysql.connector
from .routes.book_routes import bp as book_routes_bp
def create_app():
    app = Flask(__name__)
    
    app.config['DB_CONNECTION'] = mysql.connector.connect(
        host="localhost",
        user="jains",  #add mysql user
        password="Sar@7024++", #password
        database="library_management" #ensure db exists
    )

    with app.app_context():
        from .routes import book_routes
        app.register_blueprint(book_routes.bp)

    return app
