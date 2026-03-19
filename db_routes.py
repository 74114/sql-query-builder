from flask import Blueprint, request, jsonify
import mysql.connector
from database import set_connection_config

db_bp = Blueprint("db", __name__)


# POST /api/db/connect
@db_bp.route("/connect", methods=["POST"])
def connect():
    body = request.get_json(force=True, silent=True) or {}
    host     = body.get("host",     "localhost")
    port     = int(body.get("port", 3306))
    user     = body.get("user",     "root")
    password = body.get("password", "")
    database = body.get("database", "sqlcraft")

    # test the connection first
    try:
        conn = mysql.connector.connect(
            host=host, port=port,
            user=user, password=password,
            database=database,
            connection_timeout=5,
        )
        conn.close()
    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": str(e)}), 400

    # save config for future queries
    set_connection_config(host, port, user, password, database)

    return jsonify({
        "success": True,
        "message": f"Connected to {user}@{host}:{port}/{database}"
    })


# POST /api/db/disconnect
@db_bp.route("/disconnect", methods=["POST"])
def disconnect():
    set_connection_config(None, None, None, None, None)
    return jsonify({"success": True, "message": "Disconnected"})