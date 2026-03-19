from flask import Blueprint, request, jsonify, current_app
from groq_service import generate_sql
from database import run_select, save_history, mark_executed

sql_bp = Blueprint("sql", __name__)

def err(msg, code=400):
    return jsonify({"success": False, "error": msg}), code

# GET /api/sql/health
@sql_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":   "ok",
        "database": {"ok": True, "message": "Connected"},
        "model":    current_app.config.get("GROQ_MODEL"),
    }), 200

# POST /api/sql/generate
@sql_bp.route("/generate", methods=["POST"])
def generate():
    try:
        body     = request.get_json(force=True, silent=True) or {}
        question = (body.get("question") or "").strip()
        dialect  = (body.get("dialect")  or "MySQL").strip()

        if not question:
            return err("'question' is required.")

        result = generate_sql(question, dialect)
        hid    = save_history(question, dialect,
                              result["sql"], result["explanation"])

        return jsonify({
            "success":     True,
            "sql":         result["sql"],
            "explanation": result["explanation"],
            "tokens_used": result["tokens_used"],
            "model":       result["model"],
            "history_id":  hid,
        })

    except ValueError  as e: return err(str(e), 400)
    except RuntimeError as e: return err(str(e), 502)
    except Exception   as e: return err(f"Server error: {str(e)}", 500)


# POST /api/sql/execute
@sql_bp.route("/execute", methods=["POST"])
def execute():
    try:
        body = request.get_json(force=True, silent=True) or {}
        sql  = (body.get("sql") or "").strip()
        hid  = body.get("history_id")

        if not sql:
            return err("'sql' is required.")

        columns, rows, e = run_select(sql, current_app.config.get("MAX_ROWS", 500))
        if e:
            return jsonify({"success": False, "error": e}), 400

        row_count = len(rows) if rows else 0
        if hid:
            mark_executed(hid, row_count)

        return jsonify({
            "success":   True,
            "columns":   columns,
            "rows":      rows,
            "row_count": row_count,
        })
    except Exception as e:
        return err(f"Server error: {str(e)}", 500)