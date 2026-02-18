import os

from flask import Blueprint, after_this_request, jsonify, request, send_file

from models.annotation_store import AnnotationStore
from models.file_manager import FileManager
from models.pdf_processor import PdfProcessor
from models.version_store import VersionStore

files_bp = Blueprint("files", __name__)


@files_bp.route("/api/files", methods=["GET"])
def api_list_files():
    return jsonify(FileManager.list_files())


@files_bp.route("/api/files/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    user = request.form.get("user", "anonymous")
    try:
        meta = FileManager.upload(f.filename, f.stream, user)
        return jsonify(meta), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@files_bp.route("/api/files/<file_id>", methods=["GET"])
def api_get_file(file_id):
    info = FileManager.get_file_info(file_id)
    if not info:
        return jsonify({"error": "Not found"}), 404
    return jsonify(info)


@files_bp.route("/api/files/<file_id>", methods=["DELETE"])
def api_delete_file(file_id):
    user = request.args.get("user", "anonymous")
    FileManager.delete_file(file_id, user)
    return jsonify({"ok": True})


@files_bp.route("/api/files/<file_id>/download")
def api_download(file_id):
    mode = request.args.get("mode", "current")
    if mode == "original":
        path = VersionStore.get_original_path(file_id)
    else:
        path = VersionStore.get_current_path(file_id)
    if not path or not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    info = VersionStore.get_metadata(file_id)
    return send_file(path, as_attachment=True, download_name=info["original_name"])


@files_bp.route("/api/files/<file_id>/export-annotated", methods=["POST"])
def api_export_annotated(file_id):
    data = request.get_json() or {}
    users = data.get("users", [])
    fabric_overlays = data.get("fabric_overlays", [])  # [{page, user, png: data-url}]

    src = VersionStore.get_current_path(file_id)
    if not src or not os.path.exists(src):
        return jsonify({"error": "File not found"}), 404

    # Collect text overlay layers from annotation store for selected users
    layers = []
    for user in users:
        anno = AnnotationStore.get(file_id, user)
        for overlay in anno.get("text_overlays", []):
            layers.append({"type": "text", **overlay})

    # Add client-rendered Fabric PNG overlays
    for fo in fabric_overlays:
        layers.append({"type": "image", "page": fo["page"], "png": fo["png"]})

    try:
        out_path = PdfProcessor.apply_annotation_layers(src, layers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    @after_this_request
    def _cleanup(response):
        try:
            if os.path.exists(out_path):
                os.unlink(out_path)
        except Exception:
            pass
        return response

    info = VersionStore.get_metadata(file_id)
    base_name = info["original_name"].rsplit(".", 1)[0] if info else "document"
    return send_file(
        out_path,
        as_attachment=True,
        download_name=f"{base_name}_annotated.pdf",
        mimetype="application/pdf",
    )


@files_bp.route("/api/files/<file_id>/reset", methods=["POST"])
def api_reset_file(file_id):
    user = (request.get_json(silent=True) or {}).get("user", "anonymous")
    try:
        FileManager.reset_to_original(file_id, user)
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
