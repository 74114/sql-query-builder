from flask import Blueprint, jsonify, request
from database import get_history, get_history_item, delete_history_item, clear_all_history

history_bp = Blueprint("history", __name__)


@history_bp.route("/", methods=["GET"])
def list_all():
    limit  = min(int(request.args.get("limit",  50)), 200)
    offset = max(int(request.args.get("offset",  0)),   0)
    rows   = get_history(limit, offset)
    return jsonify({"success": True, "data": rows})


@history_bp.route("/<int:rid>", methods=["GET"])
def get_one(rid):
    row = get_history_item(rid)
    if not row:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True, "data": row})


@history_bp.route("/<int:rid>", methods=["DELETE"])
def delete_one(rid):
    delete_history_item(rid)
    return jsonify({"success": True})


@history_bp.route("/", methods=["DELETE"])
def delete_all():
    clear_all_history()
    return jsonify({"success": True})