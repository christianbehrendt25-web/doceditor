from flask import Blueprint, jsonify, request

from models.audit_logger import AuditLogger
from models.file_manager import FileManager
from models.version_store import VersionStore

version_bp = Blueprint("versions", __name__)


@version_bp.route("/api/files/<file_id>/versions")
def list_versions(file_id):
    meta = VersionStore.get_metadata(file_id)
    if not meta:
        return jsonify({"error": "Not found"}), 404
    return jsonify(meta["versions"])


@version_bp.route("/api/files/<file_id>/revert/<int:version>", methods=["POST"])
def revert_version(file_id, version):
    user = request.get_json(silent=True) or {}
    user = user.get("user", "anonymous")
    try:
        v = FileManager.revert(file_id, version, user)
        return jsonify({"version": v})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@version_bp.route("/api/audit-log")
def audit_log():
    limit = request.args.get("limit", 100, type=int)
    file_id = request.args.get("file_id", "")
    entries = AuditLogger.get_log(limit, file_id)
    return jsonify(entries)
