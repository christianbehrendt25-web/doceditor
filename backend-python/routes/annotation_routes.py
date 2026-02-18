from flask import Blueprint, jsonify, request

from models.annotation_store import AnnotationStore

annotation_bp = Blueprint("annotations", __name__)


@annotation_bp.route("/api/files/<file_id>/annotations")
def list_annotations(file_id):
    """Return all annotation layers for this file (one per user)."""
    users = AnnotationStore.list_users(file_id)
    result = [AnnotationStore.get(file_id, u) for u in users]
    return jsonify(result)


@annotation_bp.route("/api/files/<file_id>/annotations/<user>")
def get_annotation(file_id, user):
    return jsonify(AnnotationStore.get(file_id, user))


@annotation_bp.route("/api/files/<file_id>/annotations/<user>", methods=["PUT"])
def save_annotation(file_id, user):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Body must be a JSON object"}), 400
    AnnotationStore.save(file_id, user, data)
    return jsonify({"ok": True})


@annotation_bp.route("/api/files/<file_id>/annotations/<user>", methods=["DELETE"])
def delete_annotation(file_id, user):
    AnnotationStore.delete(file_id, user)
    return jsonify({"ok": True})
