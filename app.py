from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from database import init_db
from sql_routes import sql_bp
from history_routes import history_bp
from db_routes import db_bp
import os

def create_app():
    app = Flask(__name__, static_folder=".", static_url_path="")
    app.config.from_object(Config)
    CORS(app, origins="*")

    app.register_blueprint(sql_bp,     url_prefix="/api/sql")
    app.register_blueprint(history_bp, url_prefix="/api/history")
    app.register_blueprint(db_bp,      url_prefix="/api/db")

    @app.route("/")
    def index():
        return send_from_directory(".", "index.html")

    with app.app_context():
        init_db()

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)