import os

from flask import Blueprint, jsonify, request, render_template, send_file, abort

from models.file_manager import FileManager

files_bp = Blueprint("files", __name__)


@files_bp.route("/")
def index():
    return render_template("index.html")


@files_bp.route("/view/<file_id>")
def view_file(file_id):
    info = FileManager.get_file_info(file_id)
    if not info:
        abort(404)
    if info["file_type"] == "pdf":
        return render_template("pdf_viewer.html", file=info)
    return render_template("image_editor.html", file=info)


# --- API ---

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
        meta = FileManager.upload(f, user)
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
@files_bp.route("/api/files/<file_id>/download/<int:version>")
def api_download(file_id, version=None):
    path = FileManager.get_file_path(file_id, version)
    if not path or not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    info = FileManager.get_file_info(file_id)
    return send_file(path, as_attachment=True, download_name=info["original_name"])
