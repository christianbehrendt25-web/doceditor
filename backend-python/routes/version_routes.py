from flask import Blueprint, jsonify, request

from models.audit_logger import AuditLogger

version_bp = Blueprint("versions", __name__)


@version_bp.route("/api/audit-log")
def audit_log():
    limit = request.args.get("limit", 100, type=int)
    file_id = request.args.get("file_id", "")
    entries = AuditLogger.get_log(limit, file_id)
    return jsonify(entries)
